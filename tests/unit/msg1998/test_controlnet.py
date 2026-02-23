"""
Unit tests for MSG 1998 ControlNet module.

Tests ControlNet configuration and validation without SD pipeline.
"""

import pytest
from pathlib import Path

from lib.msg1998.controlnet import (
    DEFAULT_MODELS,
    load_controlnet_models,
    prepare_depth_map,
    prepare_normal_map,
    create_controlnet_preprocessor_config,
    get_controlnet_pipeline_config,
    validate_controlnet_input,
)
from lib.msg1998.types import ControlNetConfig


class TestDefaultModels:
    """Tests for DEFAULT_MODELS constant."""

    def test_has_depth_model(self):
        """Test that depth model is defined."""
        assert "depth" in DEFAULT_MODELS
        assert "control_v11" in DEFAULT_MODELS["depth"]

    def test_has_normal_model(self):
        """Test that normal model is defined."""
        assert "normal" in DEFAULT_MODELS
        assert "control_v11" in DEFAULT_MODELS["normal"]

    def test_has_canny_model(self):
        """Test that canny model is defined."""
        assert "canny" in DEFAULT_MODELS
        assert "control_v11" in DEFAULT_MODELS["canny"]


class TestLoadControlnetModels:
    """Tests for load_controlnet_models function."""

    def test_default_config(self):
        """Test with default configuration."""
        config = ControlNetConfig()
        models = load_controlnet_models(config)

        assert "depth" in models
        assert "normal" in models
        assert "canny" in models

    def test_depth_model_config(self):
        """Test depth model configuration."""
        config = ControlNetConfig(
            depth_model="custom_depth_model",
            depth_weight=1.5,
            guidance_start=0.1,
            guidance_end=0.9
        )
        models = load_controlnet_models(config)

        assert models["depth"]["model"] == "custom_depth_model"
        assert models["depth"]["weight"] == 1.5
        assert models["depth"]["guidance_start"] == 0.1
        assert models["depth"]["guidance_end"] == 0.9

    def test_normal_model_config(self):
        """Test normal model configuration."""
        config = ControlNetConfig(
            normal_model="custom_normal_model",
            normal_weight=0.6,
            guidance_end=1.0
        )
        models = load_controlnet_models(config)

        assert models["normal"]["model"] == "custom_normal_model"
        assert models["normal"]["weight"] == 0.6
        # Normal guidance_end is capped at 0.8
        assert models["normal"]["guidance_end"] == 0.8

    def test_canny_model_config(self):
        """Test canny model configuration."""
        config = ControlNetConfig(
            canny_model="custom_canny_model",
            canny_weight=0.7,
            canny_enabled=True
        )
        models = load_controlnet_models(config)

        assert models["canny"]["model"] == "custom_canny_model"
        assert models["canny"]["weight"] == 0.7
        assert models["canny"]["enabled"] is True

    def test_canny_disabled(self):
        """Test canny when disabled."""
        config = ControlNetConfig(canny_enabled=False)
        models = load_controlnet_models(config)

        assert models["canny"]["enabled"] is False


class TestPrepareDepthMap:
    """Tests for prepare_depth_map function."""

    def test_file_not_found(self, tmp_path):
        """Test with non-existent file."""
        nonexistent = tmp_path / "nonexistent.exr"
        output_dir = tmp_path / "output"

        with pytest.raises(FileNotFoundError):
            prepare_depth_map(nonexistent, output_dir)

    def test_creates_output_directory(self, mock_depth_exr, tmp_path):
        """Test that output directory is created."""
        output_dir = tmp_path / "new_output"

        result = prepare_depth_map(mock_depth_exr, output_dir)

        assert output_dir.exists()

    def test_output_path_generation(self, mock_depth_exr, tmp_path):
        """Test output path is generated correctly."""
        output_dir = tmp_path / "output"

        result = prepare_depth_map(mock_depth_exr, output_dir)

        assert result.suffix == ".png"
        assert "_controlnet" in result.stem
        assert result.parent == output_dir

    def test_default_parameters(self, mock_depth_exr, tmp_path):
        """Test with default parameters."""
        output_dir = tmp_path / "output"

        result = prepare_depth_map(
            mock_depth_exr,
            output_dir,
            invert=False,
            normalize=True
        )

        assert result is not None

    def test_invert_parameter(self, mock_depth_exr, tmp_path):
        """Test with invert parameter."""
        output_dir = tmp_path / "output"

        result = prepare_depth_map(
            mock_depth_exr,
            output_dir,
            invert=True
        )

        assert result is not None


class TestPrepareNormalMap:
    """Tests for prepare_normal_map function."""

    def test_file_not_found(self, tmp_path):
        """Test with non-existent file."""
        nonexistent = tmp_path / "nonexistent.exr"
        output_dir = tmp_path / "output"

        with pytest.raises(FileNotFoundError):
            prepare_normal_map(nonexistent, output_dir)

    def test_creates_output_directory(self, mock_normal_exr, tmp_path):
        """Test that output directory is created."""
        output_dir = tmp_path / "new_output"

        result = prepare_normal_map(mock_normal_exr, output_dir)

        assert output_dir.exists()

    def test_output_path_generation(self, mock_normal_exr, tmp_path):
        """Test output path is generated correctly."""
        output_dir = tmp_path / "output"

        result = prepare_normal_map(mock_normal_exr, output_dir)

        assert result.suffix == ".png"
        assert "_controlnet" in result.stem

    def test_swap_channels_parameter(self, mock_normal_exr, tmp_path):
        """Test with swap_channels parameter."""
        output_dir = tmp_path / "output"

        result = prepare_normal_map(
            mock_normal_exr,
            output_dir,
            swap_channels=True
        )

        assert result is not None


class TestCreateControlnetPreprocessorConfig:
    """Tests for create_controlnet_preprocessor_config function."""

    def test_returns_dict(self):
        """Test that function returns dictionary."""
        config = create_controlnet_preprocessor_config()

        assert isinstance(config, dict)

    def test_has_depth_preprocessor(self):
        """Test depth preprocessor configuration."""
        config = create_controlnet_preprocessor_config()

        assert "depth" in config
        assert "preprocessor" in config["depth"]
        assert "resolution" in config["depth"]
        assert config["depth"]["resolution"] == 512

    def test_has_normal_preprocessor(self):
        """Test normal preprocessor configuration."""
        config = create_controlnet_preprocessor_config()

        assert "normal" in config
        assert config["normal"]["preprocessor"] == "normalbae"

    def test_has_canny_preprocessor(self):
        """Test canny preprocessor configuration."""
        config = create_controlnet_preprocessor_config()

        assert "canny" in config
        assert "low_threshold" in config["canny"]
        assert "high_threshold" in config["canny"]

    def test_canny_thresholds(self):
        """Test canny threshold values."""
        config = create_controlnet_preprocessor_config()

        assert config["canny"]["low_threshold"] == 100
        assert config["canny"]["high_threshold"] == 200
        assert config["canny"]["low_threshold"] < config["canny"]["high_threshold"]


class TestGetControlnetPipelineConfig:
    """Tests for get_controlnet_pipeline_config function."""

    def test_default_config(self):
        """Test with default configuration."""
        config = ControlNetConfig()
        pipeline = get_controlnet_pipeline_config(config)

        assert "controlnet" in pipeline
        assert "preprocessors" in pipeline
        assert "settings" in pipeline

    def test_includes_models(self):
        """Test that models are included."""
        config = ControlNetConfig()
        pipeline = get_controlnet_pipeline_config(config)

        assert "depth" in pipeline["controlnet"]
        assert "normal" in pipeline["controlnet"]
        assert "canny" in pipeline["controlnet"]

    def test_includes_preprocessors(self):
        """Test that preprocessors are included."""
        config = ControlNetConfig()
        pipeline = get_controlnet_pipeline_config(config)

        assert "depth" in pipeline["preprocessors"]
        assert "normal" in pipeline["preprocessors"]
        assert "canny" in pipeline["preprocessors"]

    def test_settings_preprocess_flags(self):
        """Test preprocess settings."""
        config = ControlNetConfig()
        pipeline = get_controlnet_pipeline_config(
            config,
            preprocess_depth=True,
            preprocess_normal=False
        )

        assert pipeline["settings"]["preprocess_depth"] is True
        assert pipeline["settings"]["preprocess_normal"] is False

    def test_default_settings(self):
        """Test default settings values."""
        config = ControlNetConfig()
        pipeline = get_controlnet_pipeline_config(config)

        assert pipeline["settings"]["guess_mode"] is False
        assert pipeline["settings"]["pixel_perfect"] is True


class TestValidateControlnetInput:
    """Tests for validate_controlnet_input function."""

    def test_no_errors_with_valid_inputs(self, mock_depth_exr, mock_normal_exr, tmp_path):
        """Test with all valid inputs."""
        config = ControlNetConfig(depth_weight=1.0, normal_weight=0.8)

        errors = validate_controlnet_input(mock_depth_exr, mock_normal_exr, config)

        assert errors == []

    def test_missing_depth_path(self):
        """Test with missing depth path."""
        config = ControlNetConfig(depth_weight=1.0, normal_weight=0.0)

        errors = validate_controlnet_input(None, None, config)

        assert len(errors) == 1
        assert "Depth" in errors[0]

    def test_missing_normal_path(self):
        """Test with missing normal path."""
        config = ControlNetConfig(depth_weight=0.0, normal_weight=0.8)

        errors = validate_controlnet_input(None, None, config)

        assert len(errors) == 1
        assert "Normal" in errors[0]

    def test_nonexistent_depth_file(self, tmp_path):
        """Test with non-existent depth file."""
        nonexistent = tmp_path / "nonexistent.exr"
        config = ControlNetConfig(depth_weight=1.0, normal_weight=0.0)

        errors = validate_controlnet_input(nonexistent, None, config)

        assert len(errors) == 1
        assert "not found" in errors[0]

    def test_nonexistent_normal_file(self, mock_depth_exr, tmp_path):
        """Test with non-existent normal file."""
        nonexistent = tmp_path / "nonexistent.exr"
        config = ControlNetConfig(depth_weight=1.0, normal_weight=0.8)

        errors = validate_controlnet_input(mock_depth_exr, nonexistent, config)

        assert len(errors) == 1
        assert "Normal" in errors[0]

    def test_zero_weight_skips_validation(self, mock_depth_exr, mock_normal_exr):
        """Test that zero weight skips validation."""
        config = ControlNetConfig(depth_weight=0.0, normal_weight=0.0)

        # Pass None - should not error because weights are 0
        errors = validate_controlnet_input(None, None, config)

        assert errors == []

    def test_multiple_errors(self, tmp_path):
        """Test with multiple validation errors."""
        config = ControlNetConfig(depth_weight=1.0, normal_weight=0.8)

        errors = validate_controlnet_input(None, None, config)

        assert len(errors) == 2


class TestControlNetConfigDataclass:
    """Tests for ControlNetConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ControlNetConfig()

        assert config.depth_model == "control_v11f1p_sd15_depth"
        assert config.depth_weight == 1.0
        assert config.normal_model == "control_v11p_sd15_normalbae"
        assert config.normal_weight == 0.8
        assert config.guidance_start == 0.0
        assert config.guidance_end == 1.0
        assert config.canny_enabled is False

    def test_custom_values(self):
        """Test custom configuration values."""
        config = ControlNetConfig(
            depth_model="custom_depth",
            depth_weight=1.5,
            normal_weight=0.5,
            guidance_start=0.1,
            guidance_end=0.9,
            canny_enabled=True
        )

        assert config.depth_model == "custom_depth"
        assert config.depth_weight == 1.5
        assert config.guidance_start == 0.1
        assert config.guidance_end == 0.9
        assert config.canny_enabled is True

    def test_weight_ranges(self):
        """Test weight values can be various ranges."""
        # Weights can technically be any float
        config = ControlNetConfig(
            depth_weight=0.0,  # Disabled
            normal_weight=2.0,  # Strong
            canny_weight=-0.5   # Negative (unusual but valid)
        )

        assert config.depth_weight == 0.0
        assert config.normal_weight == 2.0
        assert config.canny_weight == -0.5
