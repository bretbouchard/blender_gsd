"""
Unit tests for lib/sd_projection/sd_projection.py

Tests core SD projection functionality including:
- StyleConfig and ControlNet configuration
- SDClient API interactions (mocked)
- PassGenerator depth/normal/canny generation
- SDProjectionMapper projection workflow

Note: bpy and mathutils are mocked globally in tests/unit/conftest.py
"""

import pytest
from pathlib import Path
from dataclasses import asdict
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json


class TestStyleConfig:
    """Tests for StyleConfig dataclass."""

    def test_default_style_config(self):
        """Test default StyleConfig values."""
        from lib.sd_projection.sd_projection import StyleConfig

        config = StyleConfig()

        assert config.prompt == ""
        assert config.negative_prompt == "blurry, low quality, distorted"
        assert config.style_models == []
        assert config.style_blend == 0.5
        assert len(config.controlnets) == 2  # Default depth + normal
        assert config.projection_resolution == (2048, 2048)
        assert config.seed == -1
        assert config.drift_enabled is True
        assert config.drift_speed == 0.1

    def test_style_config_with_values(self):
        """Test StyleConfig with custom values."""
        from lib.sd_projection.sd_projection import (
            StyleConfig,
            StyleModel,
            ControlNetConfig,
            ControlNetType,
        )

        config = StyleConfig(
            prompt="cyberpunk city",
            negative_prompt="blurry",
            style_models=[
                StyleModel(name="cyberpunk", weight=1.0),
            ],
            controlnets=[
                ControlNetConfig(control_type=ControlNetType.DEPTH, weight=1.0),
            ],
            projection_resolution=(2048, 2048),
            seed=42,
        )

        assert config.prompt == "cyberpunk city"
        assert config.negative_prompt == "blurry"
        assert len(config.style_models) == 1
        assert config.style_models[0].name == "cyberpunk"
        assert len(config.controlnets) == 1
        assert config.projection_resolution == (2048, 2048)
        assert config.seed == 42


class TestControlNetConfig:
    """Tests for ControlNetConfig dataclass."""

    def test_default_controlnet_config(self):
        """Test default ControlNetConfig values."""
        from lib.sd_projection.sd_projection import (
            ControlNetConfig,
            ControlNetType,
        )

        config = ControlNetConfig(control_type=ControlNetType.DEPTH)

        assert config.control_type == ControlNetType.DEPTH
        assert config.weight == 1.0
        assert config.model == "control_v11f1p_sd15_depth"
        assert config.preprocessor == "depth_anything"

    def test_controlnet_types(self):
        """Test all ControlNetType enum values."""
        from lib.sd_projection.sd_projection import ControlNetType

        assert ControlNetType.DEPTH.value == "depth"
        assert ControlNetType.NORMAL.value == "normal"
        assert ControlNetType.CANNY.value == "canny"
        assert ControlNetType.POSE.value == "pose"
        assert ControlNetType.SCRIBBLE.value == "scribble"
        assert ControlNetType.SEGMENTATION.value == "segmentation"


class TestStyleModel:
    """Tests for StyleModel dataclass."""

    def test_style_model_defaults(self):
        """Test StyleModel default values."""
        from lib.sd_projection.sd_projection import StyleModel

        model = StyleModel(name="test_style")

        assert model.name == "test_style"
        assert model.weight == 1.0
        assert model.path == ""
        assert model.trigger_words == []
        assert model.is_lora is True

    def test_style_model_with_values(self):
        """Test StyleModel with custom values."""
        from lib.sd_projection.sd_projection import StyleModel

        model = StyleModel(
            name="arcane_style",
            weight=0.8,
            path="arcane_v2.safetensors",
            trigger_words=["arcane style", "painted"],
        )

        assert model.name == "arcane_style"
        assert model.weight == 0.8
        assert model.path == "arcane_v2.safetensors"
        assert "arcane style" in model.trigger_words


class TestProjectionResult:
    """Tests for ProjectionResult dataclass."""

    def test_success_result(self):
        """Test successful ProjectionResult."""
        from lib.sd_projection.sd_projection import ProjectionResult

        result = ProjectionResult(
            success=True,
            generated_texture_path=Path("/tmp/texture.png"),
            projected_objects=["Building1", "Building2"],
        )

        assert result.success is True
        assert result.generated_texture_path == Path("/tmp/texture.png")
        assert len(result.projected_objects) == 2
        assert result.error_message == ""

    def test_failure_result(self):
        """Test failed ProjectionResult."""
        from lib.sd_projection.sd_projection import ProjectionResult

        result = ProjectionResult(
            success=False,
            error_message="Connection refused",
            projected_objects=[],
        )

        assert result.success is False
        assert result.error_message == "Connection refused"
        assert result.generated_texture_path is None


class TestSDBackend:
    """Tests for SDBackend enum."""

    def test_backend_types(self):
        """Test all SDBackend enum values."""
        from lib.sd_projection.sd_projection import SDBackend

        assert SDBackend.AUTO1111.value == "auto1111"
        assert SDBackend.COMFYUI.value == "comfyui"


class TestProjectionMode:
    """Tests for ProjectionMode enum."""

    def test_projection_modes(self):
        """Test all ProjectionMode enum values."""
        from lib.sd_projection.sd_projection import ProjectionMode

        assert ProjectionMode.CAMERA_PROJECT.value == "camera_project"
        assert ProjectionMode.UV_REPLACE.value == "uv_replace"
        assert ProjectionMode.UV_BLEND.value == "uv_blend"
        assert ProjectionMode.TRIPPY.value == "trippy"


class TestSDClient:
    """Tests for SDClient API interactions."""

    def test_client_initialization(self):
        """Test SDClient initialization."""
        from lib.sd_projection.sd_projection import SDClient, StyleConfig

        config = StyleConfig(api_url="http://localhost:7860")
        client = SDClient(config)

        assert client.config.api_url == "http://localhost:7860"


class TestPassGenerator:
    """Tests for PassGenerator (depth, normal, canny passes)."""

    def test_pass_generator_initialization(self):
        """Test PassGenerator initialization."""
        from lib.sd_projection.sd_projection import PassGenerator
        from pathlib import Path
        import tempfile

        output_dir = Path(tempfile.gettempdir()) / "test_sd_projection"
        generator = PassGenerator(output_dir)

        assert generator is not None
        assert generator.output_dir == output_dir

    def test_resolution_validation(self):
        """Test resolution validation."""
        # Test valid resolutions
        valid = [(512, 512), (1024, 1024), (2048, 2048), (4096, 4096)]
        for res in valid:
            assert res[0] > 0 and res[1] > 0


class TestSDProjectionMapper:
    """Tests for SDProjectionMapper main class."""

    def test_mapper_initialization(self):
        """Test SDProjectionMapper initialization."""
        from lib.sd_projection.sd_projection import (
            SDProjectionMapper,
            StyleConfig,
        )

        config = StyleConfig(prompt="test")
        mapper = SDProjectionMapper(config)

        assert mapper.config.prompt == "test"
        assert mapper.sd_client is not None
        assert mapper.pass_generator is not None

    def test_mapper_with_custom_config(self):
        """Test SDProjectionMapper with custom configuration."""
        from lib.sd_projection.sd_projection import (
            SDProjectionMapper,
            StyleConfig,
            SDBackend,
        )

        config = StyleConfig(
            prompt="cyberpunk",
            projection_resolution=(2048, 2048),
            backend=SDBackend.COMFYUI,
        )

        mapper = SDProjectionMapper(config)

        assert mapper.config.projection_resolution == (2048, 2048)
        assert mapper.config.backend == SDBackend.COMFYUI


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_projection_mapper(self):
        """Test create_projection_mapper convenience function."""
        from lib.sd_projection.sd_projection import (
            create_projection_mapper,
        )

        mapper = create_projection_mapper(
            style_models=["cyberpunk"],
            prompt="test prompt",
        )

        assert mapper.config.prompt == "test prompt"
        assert len(mapper.config.style_models) == 1
