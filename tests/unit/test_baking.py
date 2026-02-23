"""
Texture Baking Module Unit Tests

Tests for: lib/cinematic/projection/baking.py
Coverage target: 80%+

Part of Phase 9.3 - Texture Baking (REQ-ANAM-04)
Beads: blender_gsd-37
"""

import pytest
import math
from lib.oracle import compare_numbers, compare_vectors

from lib.cinematic.projection.baking import (
    BakeMode,
    BakeFormat,
    BakeConfig,
    BakeResult,
    bake_projection_texture,
    bake_object_texture,
    create_bake_material,
    prepare_for_baking,
    cleanup_bake_artifacts,
    export_baked_textures,
)

from lib.cinematic.projection.types import (
    ProjectionMode,
    AnamorphicProjectionConfig,
)


class TestBakeMode:
    """Unit tests for BakeMode constants."""

    def test_all_modes_exist(self):
        """All expected bake modes should be defined."""
        assert hasattr(BakeMode, 'DIFFUSE')
        assert hasattr(BakeMode, 'EMISSION')
        assert hasattr(BakeMode, 'DECAL')
        assert hasattr(BakeMode, 'COMBINED')
        assert hasattr(BakeMode, 'SHADOW')

    def test_mode_values(self):
        """Mode values should be strings."""
        assert BakeMode.DIFFUSE == "diffuse"
        assert BakeMode.EMISSION == "emission"
        assert BakeMode.DECAL == "decal"
        assert BakeMode.COMBINED == "combined"
        assert BakeMode.SHADOW == "shadow"


class TestBakeFormat:
    """Unit tests for BakeFormat constants."""

    def test_all_formats_exist(self):
        """All expected formats should be defined."""
        assert hasattr(BakeFormat, 'PNG')
        assert hasattr(BakeFormat, 'JPEG')
        assert hasattr(BakeFormat, 'TARGA')
        assert hasattr(BakeFormat, 'OPEN_EXR')
        assert hasattr(BakeFormat, 'TIFF')

    def test_format_values(self):
        """Format values should be strings."""
        assert BakeFormat.PNG == "PNG"
        assert BakeFormat.JPEG == "JPEG"
        assert BakeFormat.TARGA == "TARGA"
        assert BakeFormat.OPEN_EXR == "OPEN_EXR"
        assert BakeFormat.TIFF == "TIFF"


class TestBakeConfig:
    """Unit tests for BakeConfig dataclass."""

    def test_default_values(self):
        """Default config should have sensible values."""
        config = BakeConfig()

        assert config.resolution_x == 2048
        assert config.resolution_y == 2048
        assert config.bake_mode == BakeMode.EMISSION
        assert config.output_format == BakeFormat.PNG
        assert config.uv_layer == "ProjectionUV"
        assert config.margin == 16
        assert config.samples == 4
        assert config.non_destructive is True

    def test_custom_values(self):
        """Custom values should be stored."""
        config = BakeConfig(
            resolution_x=4096,
            resolution_y=4096,
            bake_mode=BakeMode.DIFFUSE,
            output_format=BakeFormat.OPEN_EXR,
            samples=16,
        )

        assert config.resolution_x == 4096
        assert config.resolution_y == 4096
        assert config.bake_mode == BakeMode.DIFFUSE
        assert config.output_format == BakeFormat.OPEN_EXR
        assert config.samples == 16

    def test_to_dict(self):
        """to_dict should serialize all fields."""
        config = BakeConfig(
            resolution_x=1024,
            resolution_y=1024,
            bake_mode=BakeMode.DECAL,
        )

        data = config.to_dict()

        assert data["resolution_x"] == 1024
        assert data["resolution_y"] == 1024
        assert data["bake_mode"] == BakeMode.DECAL
        assert "output_format" in data
        assert "uv_layer" in data

    def test_from_dict(self):
        """from_dict should deserialize correctly."""
        data = {
            "resolution_x": 512,
            "resolution_y": 512,
            "bake_mode": BakeMode.SHADOW,
            "output_format": BakeFormat.TARGA,
            "margin": 32,
            "samples": 8,
        }

        config = BakeConfig.from_dict(data)

        assert config.resolution_x == 512
        assert config.resolution_y == 512
        assert config.bake_mode == BakeMode.SHADOW
        assert config.output_format == BakeFormat.TARGA
        assert config.margin == 32
        assert config.samples == 8

    def test_serialization_round_trip(self):
        """Round-trip serialization should preserve values."""
        original = BakeConfig(
            resolution_x=2048,
            resolution_y=2048,
            bake_mode=BakeMode.COMBINED,
            output_format=BakeFormat.TIFF,
            margin=8,
            samples=4,
            non_destructive=False,
        )

        restored = BakeConfig.from_dict(original.to_dict())

        assert restored.resolution_x == original.resolution_x
        assert restored.resolution_y == original.resolution_y
        assert restored.bake_mode == original.bake_mode
        assert restored.output_format == original.output_format
        assert restored.margin == original.margin


class TestBakeResult:
    """Unit tests for BakeResult dataclass."""

    def test_default_values(self):
        """Default result should have empty/safe values."""
        result = BakeResult(
            object_name="",
            texture_path="",
            texture_name="",
            material_name="",
            resolution=(2048, 2048),
            bake_mode=BakeMode.EMISSION,
            bake_time=0.0,
            success=False,
        )

        assert result.object_name == ""
        assert result.texture_path == ""
        assert result.success is False
        assert result.bake_time == 0.0

    def test_successful_result(self):
        """Successful result should store all data."""
        result = BakeResult(
            object_name="Floor",
            texture_path="/textures/floor_baked.png",
            texture_name="Floor_baked",
            material_name="Floor_emission_material",
            resolution=(2048, 2048),
            bake_mode=BakeMode.EMISSION,
            bake_time=2.5,
            success=True,
            warnings=["Minor UV overlap detected"],
        )

        assert result.object_name == "Floor"
        assert result.texture_path == "/textures/floor_baked.png"
        assert result.success is True
        compare_numbers(result.bake_time, 2.5)
        assert len(result.warnings) == 1

    def test_failed_result(self):
        """Failed result should store error message."""
        result = BakeResult(
            object_name="MissingObject",
            texture_path="",
            texture_name="",
            material_name="",
            resolution=(0, 0),
            bake_mode=BakeMode.DIFFUSE,
            bake_time=0.0,
            success=False,
            error_message="Object not found",
        )

        assert result.success is False
        assert "not found" in result.error_message

    def test_to_dict(self):
        """to_dict should serialize all fields."""
        result = BakeResult(
            object_name="Wall",
            texture_path="/textures/wall.png",
            texture_name="Wall_baked",
            material_name="Wall_material",
            resolution=(1024, 1024),
            bake_mode=BakeMode.DECAL,
            bake_time=1.5,
            success=True,
        )

        data = result.to_dict()

        assert data["object_name"] == "Wall"
        assert data["texture_path"] == "/textures/wall.png"
        assert data["resolution"] == [1024, 1024]
        assert data["bake_mode"] == BakeMode.DECAL
        assert data["success"] is True

    def test_from_dict(self):
        """from_dict should deserialize correctly."""
        data = {
            "object_name": "Ceiling",
            "texture_path": "/path/to/ceiling.png",
            "texture_name": "Ceiling_baked",
            "material_name": "Ceiling_mat",
            "resolution": [512, 512],
            "bake_mode": BakeMode.COMBINED,
            "bake_time": 3.2,
            "success": True,
            "error_message": "",
            "warnings": ["Warning 1", "Warning 2"],
        }

        result = BakeResult.from_dict(data)

        assert result.object_name == "Ceiling"
        assert result.resolution == (512, 512)
        compare_numbers(result.bake_time, 3.2)
        assert result.success is True
        assert len(result.warnings) == 2


class TestBakeProjectionTexture:
    """Unit tests for bake_projection_texture function."""

    @pytest.mark.skip(reason="Requires real Blender (bpy is mocked in test environment)")
    def test_requires_blender(self):
        """Should raise RuntimeError without Blender."""
        config = AnamorphicProjectionConfig(
            source_image="test.png",
            camera_name="Camera",
        )

        with pytest.raises(RuntimeError) as exc_info:
            bake_projection_texture(config)

        assert "Blender required" in str(exc_info.value)


class TestBakeObjectTexture:
    """Unit tests for bake_object_texture function."""

    @pytest.mark.skip(reason="Requires real Blender (bpy is mocked in test environment)")
    def test_requires_blender(self):
        """Should raise RuntimeError without Blender."""
        with pytest.raises(RuntimeError) as exc_info:
            bake_object_texture("Floor", "test.png", "Camera")

        assert "Blender required" in str(exc_info.value)


class TestCreateBakeMaterial:
    """Unit tests for create_bake_material function."""

    @pytest.mark.skip(reason="Requires real Blender (bpy is mocked in test environment)")
    def test_requires_blender(self):
        """Should raise RuntimeError without Blender."""
        with pytest.raises(RuntimeError) as exc_info:
            create_bake_material("Floor", "/path/to/texture.png")

        assert "Blender required" in str(exc_info.value)


class TestPrepareForBaking:
    """Unit tests for prepare_for_baking function."""

    @pytest.mark.skip(reason="Requires real Blender (bpy is mocked in test environment)")
    def test_requires_blender(self):
        """Should raise RuntimeError without Blender."""
        with pytest.raises(RuntimeError) as exc_info:
            prepare_for_baking(["Floor"])

        assert "Blender required" in str(exc_info.value)


class TestCleanupBakeArtifacts:
    """Unit tests for cleanup_bake_artifacts function."""

    @pytest.mark.skip(reason="Requires real Blender (bpy is mocked in test environment)")
    def test_requires_blender(self):
        """Should raise RuntimeError without Blender."""
        with pytest.raises(RuntimeError) as exc_info:
            cleanup_bake_artifacts()

        assert "Blender required" in str(exc_info.value)


class TestExportBakedTextures:
    """Unit tests for export_baked_textures function."""

    @pytest.mark.skip(reason="Requires real Blender (bpy is mocked in test environment)")
    def test_requires_blender(self):
        """Should raise RuntimeError without Blender."""
        with pytest.raises(RuntimeError) as exc_info:
            export_baked_textures("/output/path")

        assert "Blender required" in str(exc_info.value)


class TestModuleImports:
    """Tests for module-level imports."""

    def test_baking_module_imports(self):
        """All baking types should be importable."""
        from lib.cinematic.projection.baking import (
            BakeMode,
            BakeFormat,
            BakeConfig,
            BakeResult,
            bake_projection_texture,
            bake_object_texture,
            create_bake_material,
            prepare_for_baking,
            cleanup_bake_artifacts,
            export_baked_textures,
        )

        assert BakeMode is not None
        assert BakeFormat is not None
        assert BakeConfig is not None
        assert callable(bake_projection_texture)
        assert callable(create_bake_material)

    def test_package_imports(self):
        """All baking APIs should be importable from package."""
        from lib.cinematic.projection import (
            BakeMode,
            BakeFormat,
            BakeConfig,
            BakeResult,
            bake_projection_texture,
            bake_object_texture,
            create_bake_material,
            prepare_for_baking,
            cleanup_bake_artifacts,
            export_baked_textures,
        )

        assert BakeMode is not None
        assert BakeFormat is not None
        assert BakeConfig is not None
        assert callable(bake_projection_texture)


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
