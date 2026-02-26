"""
Unit tests for Tentacle Export Pipeline.

Tests LOD generation, FBX export configuration, and pipeline orchestration.
All tests run without Blender using numpy fallback mode.
"""

import pytest
import numpy as np
from typing import List

from lib.tentacle.export.types import (
    LODStrategy,
    ExportFormat,
    LODLevel,
    LODConfig,
    FBXExportConfig,
    MaterialSlotConfig,
    ExportPreset,
    LODResult,
    ExportResult,
    MaterialSlotResult,
    EXPORT_PRESETS,
    get_export_preset,
    list_export_presets,
)
from lib.tentacle.export.lod import (
    LODGenerator,
    generate_lods,
    generate_lod_levels,
)
from lib.tentacle.export.fbx import (
    FBXExporter,
    export_for_unreal,
)


# Test Fixtures

@pytest.fixture
def sample_vertices() -> np.ndarray:
    """Generate sample tentacle vertices for testing."""
    # Create a simple tube shape
    segments = 20
    resolution = 16
    vertices = []

    for i in range(segments + 1):
        z = i * 0.05  # Length segments
        radius = 0.04 - (0.03 * i / segments)  # Taper from 0.04 to 0.01
        for j in range(resolution):
            angle = 2 * np.pi * j / resolution
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            vertices.append([x, y, z])

    return np.array(vertices)


@pytest.fixture
def sample_faces() -> np.ndarray:
    """Generate sample faces for testing."""
    segments = 20
    resolution = 16
    faces = []

    for i in range(segments):
        for j in range(resolution):
            j_next = (j + 1) % resolution
            v1 = i * resolution + j
            v2 = i * resolution + j_next
            v3 = (i + 1) * resolution + j_next
            v4 = (i + 1) * resolution + j
            faces.append([v1, v2, v3, v4])

    return np.array(faces)


@pytest.fixture
def default_lod_config() -> LODConfig:
    """Create default LOD configuration."""
    return LODConfig()


@pytest.fixture
def default_fbx_config() -> FBXExportConfig:
    """Create default FBX export configuration."""
    return FBXExportConfig()


# Type Tests

class TestLODLevel:
    """Tests for LODLevel dataclass."""

    def test_default_values(self):
        """Test default LOD level values."""
        level = LODLevel("LOD0")
        assert level.name == "LOD0"
        assert level.ratio == 1.0
        assert level.screen_size == 1.0

    def test_custom_values(self):
        """Test custom LOD level values."""
        level = LODLevel("LOD1", ratio=0.5, screen_size=0.5)
        assert level.name == "LOD1"
        assert level.ratio == 0.5
        assert level.screen_size == 0.5

    def test_to_dict(self):
        """Test serialization to dictionary."""
        level = LODLevel("LOD2", ratio=0.25, screen_size=0.25)
        d = level.to_dict()
        assert d["name"] == "LOD2"
        assert d["ratio"] == 0.25
        assert d["screen_size"] == 0.25


class TestLODConfig:
    """Tests for LODConfig dataclass."""

    def test_default_config(self):
        """Test default LOD configuration."""
        config = LODConfig()
        assert config.enabled is True
        assert config.strategy == LODStrategy.DECIMATE
        assert len(config.levels) == 4
        assert config.preserve_uvs is True
        assert config.preserve_shape_keys is True

    def test_custom_levels(self):
        """Test custom LOD levels."""
        levels = [
            LODLevel("LOD0", 1.0, 1.0),
            LODLevel("LOD1", 0.5, 0.5),
        ]
        config = LODConfig(levels=levels)
        assert len(config.levels) == 2

    def test_to_dict(self):
        """Test serialization."""
        config = LODConfig()
        d = config.to_dict()
        assert d["enabled"] is True
        assert d["strategy"] == "decimate"
        assert len(d["levels"]) == 4


class TestFBXExportConfig:
    """Tests for FBXExportConfig dataclass."""

    def test_default_config(self):
        """Test default FBX configuration."""
        config = FBXExportConfig()
        assert config.include_shape_keys is True
        assert config.include_skinning is True
        assert config.apply_modifiers is True
        assert config.global_scale == 1.0
        assert config.tangent_space is True
        assert config.embed_textures is False

    def test_custom_config(self):
        """Test custom FBX configuration."""
        config = FBXExportConfig(
            output_path="/custom/path.fbx",
            include_shape_keys=False,
            global_scale=0.01,
        )
        assert config.output_path == "/custom/path.fbx"
        assert config.include_shape_keys is False
        assert config.global_scale == 0.01

    def test_to_dict(self):
        """Test serialization."""
        config = FBXExportConfig()
        d = config.to_dict()
        assert d["include_shape_keys"] is True
        assert d["global_scale"] == 1.0


class TestExportPreset:
    """Tests for ExportPreset dataclass."""

    def test_default_preset(self):
        """Test default preset creation."""
        preset = ExportPreset.default()
        assert preset.name == "Default"
        assert preset.format == ExportFormat.FBX
        assert preset.lod_config.enabled is True

    def test_custom_preset(self):
        """Test custom preset creation."""
        preset = ExportPreset(
            name="Custom",
            lod_config=LODConfig(enabled=False),
            output_dir="/custom/output",
        )
        assert preset.name == "Custom"
        assert preset.lod_config.enabled is False
        assert preset.output_dir == "/custom/output"


# LOD Generator Tests

class TestLODGenerator:
    """Tests for LODGenerator class."""

    def test_generate_numpy_mode(
        self,
        sample_vertices: np.ndarray,
        sample_faces: np.ndarray,
        default_lod_config: LODConfig,
    ):
        """Test LOD generation in numpy mode."""
        generator = LODGenerator(default_lod_config)
        results = generator.generate_lods(
            base_vertices=sample_vertices,
            base_faces=sample_faces,
        )

        assert len(results) == 4
        assert all(r.success for r in results)

        # LOD0 should have most triangles
        assert results[0].triangle_count > results[1].triangle_count
        assert results[1].triangle_count > results[2].triangle_count
        assert results[2].triangle_count > results[3].triangle_count

    def test_lod_screen_sizes(self, default_lod_config: LODConfig):
        """Test that screen sizes are correctly set."""
        generator = LODGenerator(default_lod_config)
        results = generator._generate_numpy(
            np.random.rand(100, 3),
            np.zeros((50, 4), dtype=int),
        )

        assert results[0].screen_size_ratio == 1.0
        assert results[1].screen_size_ratio == 0.5
        assert results[2].screen_size_ratio == 0.25
        assert results[3].screen_size_ratio == 0.12

    def test_minimum_triangle_count(self, default_lod_config: LODConfig):
        """Test that minimum triangle count is enforced."""
        generator = LODGenerator(default_lod_config)
        # Very small mesh
        results = generator._generate_numpy(
            np.random.rand(4, 3),
            np.zeros((2, 4), dtype=int),
        )

        # Should have minimum 4 triangles
        for result in results:
            assert result.triangle_count >= 4


class TestGenerateLods:
    """Tests for generate_lods convenience function."""

    def test_with_default_config(
        self,
        sample_vertices: np.ndarray,
        sample_faces: np.ndarray,
    ):
        """Test LOD generation with default config."""
        results = generate_lods(
            vertices=sample_vertices,
            faces=sample_faces,
        )
        assert len(results) == 4

    def test_with_custom_config(
        self,
        sample_vertices: np.ndarray,
        sample_faces: np.ndarray,
    ):
        """Test LOD generation with custom config."""
        custom_levels = [
            LODLevel("LOD0", 1.0, 1.0),
            LODLevel("LOD1", 0.75, 0.75),
        ]
        config = LODConfig(levels=custom_levels)
        results = generate_lods(
            vertices=sample_vertices,
            faces=sample_faces,
            config=config,
        )
        assert len(results) == 2


class TestGenerateLodLevels:
    """Tests for generate_lod_levels function."""

    def test_default_levels(self):
        """Test default LOD level generation."""
        levels = generate_lod_levels(1000)
        assert len(levels) == 4
        assert levels[0].name == "LOD0"
        assert levels[0].ratio == 1.0
        assert levels[3].ratio == 0.12

    def test_custom_level_count(self):
        """Test custom level count."""
        levels = generate_lod_levels(1000, levels=3)
        assert len(levels) == 3

    def test_remesh_strategy(self):
        """Test remesh strategy ratios."""
        levels = generate_lod_levels(
            1000,
            strategy=LODStrategy.REMESH,
        )
        # Remesh preserves more detail
        assert levels[1].ratio == 0.6
        assert levels[2].ratio == 0.35


# FBX Exporter Tests

class TestFBXExporter:
    """Tests for FBXExporter class."""

    def test_export_without_blender(self, default_fbx_config: FBXExportConfig):
        """Test export fails gracefully without Blender."""
        exporter = FBXExporter(default_fbx_config)
        result = exporter.export(mesh_obj=None)

        assert result.success is False
        assert "blender" in result.error.lower()

    def test_config_passed_to_export(self):
        """Test that configuration is used in export."""
        config = FBXExportConfig(
            output_path="/test/output.fbx",
            include_shape_keys=False,
        )
        exporter = FBXExporter(config)
        assert exporter.config.output_path == "/test/output.fbx"
        assert exporter.config.include_shape_keys is False


class TestExportForUnreal:
    """Tests for export_for_unreal convenience function."""

    def test_without_blender(self):
        """Test export fails gracefully without Blender."""
        result = export_for_unreal(
            mesh_obj=None,
            output_path="/test/output.fbx",
        )
        assert result.success is False
        assert result.error is not None


# Preset Tests

class TestExportPresets:
    """Tests for export presets."""

    def test_default_preset_exists(self):
        """Test that default preset exists."""
        preset = get_export_preset("default")
        assert preset.name == "Default Unreal Export"
        assert preset.lod_config.enabled is True

    def test_high_quality_preset(self):
        """Test high quality preset."""
        preset = get_export_preset("high_quality")
        assert preset.name == "High Quality"
        assert preset.material_config.texture_size == 4096

    def test_mobile_preset(self):
        """Test mobile optimized preset."""
        preset = get_export_preset("mobile")
        assert preset.name == "Mobile Optimized"
        assert preset.material_config.texture_size == 1024
        assert len(preset.lod_config.levels) == 3

    def test_preview_preset(self):
        """Test preview preset."""
        preset = get_export_preset("preview")
        assert preset.name == "Preview/Testing"
        assert preset.lod_config.enabled is False

    def test_list_presets(self):
        """Test listing presets."""
        presets = list_export_presets()
        assert "default" in presets
        assert "high_quality" in presets
        assert "mobile" in presets
        assert "preview" in presets

    def test_invalid_preset_raises(self):
        """Test that invalid preset raises KeyError."""
        with pytest.raises(KeyError):
            get_export_preset("invalid_preset")


# Result Tests

class TestLODResult:
    """Tests for LODResult dataclass."""

    def test_success_result(self):
        """Test successful LOD result."""
        result = LODResult(
            level_name="LOD0",
            triangle_count=1000,
            vertex_count=500,
            screen_size_ratio=1.0,
        )
        assert result.success is True
        assert result.error is None

    def test_failure_result(self):
        """Test failed LOD result."""
        result = LODResult(
            level_name="LOD1",
            triangle_count=0,
            vertex_count=0,
            screen_size_ratio=0.5,
            success=False,
            error="Decimation failed",
        )
        assert result.success is False
        assert result.error == "Decimation failed"

    def test_to_dict(self):
        """Test serialization."""
        result = LODResult(
            level_name="LOD0",
            triangle_count=1000,
            vertex_count=500,
            screen_size_ratio=1.0,
        )
        d = result.to_dict()
        assert d["level_name"] == "LOD0"
        assert d["triangle_count"] == 1000
        assert d["success"] is True


class TestExportResult:
    """Tests for ExportResult dataclass."""

    def test_success_result(self):
        """Test successful export result."""
        result = ExportResult(
            success=True,
            output_path="/output/tentacle.fbx",
            triangle_count=2000,
            vertex_count=1000,
            has_skeleton=True,
            has_morph_targets=True,
        )
        assert result.success is True
        assert result.has_skeleton is True
        assert result.has_morph_targets is True

    def test_failure_result(self):
        """Test failed export result."""
        result = ExportResult(
            success=False,
            error="Export failed",
        )
        assert result.success is False
        assert result.error == "Export failed"

    def test_to_dict(self):
        """Test serialization."""
        result = ExportResult(
            success=True,
            output_path="/output/tentacle.fbx",
            triangle_count=2000,
            file_size_bytes=102400,
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["triangle_count"] == 2000
        assert d["file_size_bytes"] == 102400


# Integration Tests

class TestExportIntegration:
    """Integration tests for export pipeline."""

    def test_full_lod_pipeline(
        self,
        sample_vertices: np.ndarray,
        sample_faces: np.ndarray,
    ):
        """Test full LOD generation pipeline."""
        # Generate LODs
        results = generate_lods(
            vertices=sample_vertices,
            faces=sample_faces,
        )

        # Verify results
        assert len(results) == 4
        assert all(r.success for r in results)

        # Verify triangle counts decrease
        for i in range(1, len(results)):
            assert results[i].triangle_count <= results[i-1].triangle_count

    def test_custom_preset_pipeline(
        self,
        sample_vertices: np.ndarray,
        sample_faces: np.ndarray,
    ):
        """Test pipeline with custom preset."""
        # Get mobile preset
        preset = get_export_preset("mobile")

        # Generate LODs with mobile config
        results = generate_lods(
            vertices=sample_vertices,
            faces=sample_faces,
            config=preset.lod_config,
        )

        # Mobile has 3 LOD levels
        assert len(results) == 3
