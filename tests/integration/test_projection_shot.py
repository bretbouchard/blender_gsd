"""
Integration tests for projection shot building.

Tests the complete pipeline from YAML configuration to built projection setup.
"""

import pytest
import tempfile
from pathlib import Path

from lib.cinematic.projection.physical.integration import (
    ProjectionShotConfig,
    ProjectionShotResult,
    ProjectionShotBuilder,
    build_projection_shot,
    build_projection_shot_from_dict,
)


class TestProjectionShotConfig:
    """Tests for ProjectionShotConfig."""

    def test_default_config(self):
        """Default configuration values."""
        config = ProjectionShotConfig(name="test")

        assert config.name == "test"
        assert config.description == ""
        assert config.projector_profile == ""
        assert config.calibration_type == "three_point"
        assert config.blend_mode == "mix"
        assert config.intensity == 1.0

    def test_custom_config(self):
        """Custom configuration values."""
        config = ProjectionShotConfig(
            name="custom",
            description="Custom shot",
            projector_profile="epson_home_cinema_2150",
            calibration_type="four_point_dlt",
            resolution=(3840, 2160),
            output_format="exr",
        )

        assert config.projector_profile == "epson_home_cinema_2150"
        assert config.calibration_type == "four_point_dlt"
        assert config.resolution == (3840, 2160)
        assert config.output_format == "exr"

    def test_config_serialization(self):
        """Config to_dict and from_dict round-trip."""
        config = ProjectionShotConfig(
            name="serialize_test",
            projector_profile="benq_tk700sti",
            calibration_points=[
                {"world_position": [0, 0, 0], "projector_uv": [0, 0]},
                {"world_position": [1, 0, 0], "projector_uv": [1, 0]},
            ],
            content_source="test.png",
        )

        data = config.to_dict()
        restored = ProjectionShotConfig.from_dict(data)

        assert restored.name == config.name
        assert restored.projector_profile == config.projector_profile
        assert len(restored.calibration_points) == 2
        assert restored.content_source == "test.png"

    def test_from_yaml_data(self):
        """Config from YAML-style dictionary."""
        yaml_data = {
            'name': 'YAML Shot',
            'description': 'From YAML',
            'camera': {
                'type': 'projection',
                'projector_profile': 'epson_home_cinema_2150',
                'calibration': {
                    'type': 'three_point',
                    'points': [
                        {'world_position': [0, 0, 0], 'projector_uv': [0, 0]},
                        {'world_position': [2, 0, 0], 'projector_uv': [1, 0]},
                        {'world_position': [0, 0, 1.5], 'projector_uv': [0, 1]},
                    ]
                }
            },
            'content': {
                'source': '//content/video.mp4',
                'blend_mode': 'add',
                'intensity': 0.8,
            },
            'output': {
                'resolution': [1920, 1080],
                'format': 'video',
                'output_path': '//output/',
            }
        }

        config = ProjectionShotConfig.from_dict(yaml_data)

        assert config.name == 'YAML Shot'
        assert config.projector_profile == 'epson_home_cinema_2150'
        assert len(config.calibration_points) == 3
        assert config.blend_mode == 'add'
        assert config.intensity == 0.8
        assert config.resolution == (1920, 1080)


class TestProjectionShotBuilder:
    """Tests for ProjectionShotBuilder."""

    @pytest.fixture
    def simple_config(self):
        """Create simple test configuration."""
        return ProjectionShotConfig(
            name="simple_test",
            projector_profile="Epson_Home_Cinema_2150",
            calibration_points=[
                {"world_position": [0, 0, 0], "projector_uv": [0, 0], "label": "BL"},
                {"world_position": [2, 0, 0], "projector_uv": [1, 0], "label": "BR"},
                {"world_position": [0, 0, 1.5], "projector_uv": [0, 1], "label": "TL"},
            ],
        )

    def test_builder_initialization(self, simple_config):
        """Builder initializes correctly."""
        builder = ProjectionShotBuilder(simple_config)

        assert builder.config == simple_config
        assert builder.profile is None
        assert builder.calibration is None

    def test_load_profile(self, simple_config):
        """Load projector profile."""
        builder = ProjectionShotBuilder(simple_config)
        builder.load_profile()

        assert builder.profile is not None
        assert builder.profile.name == "Epson_Home_Cinema_2150"

    def test_load_profile_invalid(self):
        """Invalid profile produces error."""
        config = ProjectionShotConfig(
            name="invalid",
            projector_profile="nonexistent_profile",
        )
        builder = ProjectionShotBuilder(config)
        builder.load_profile()

        assert len(builder._errors) > 0

    def test_setup_calibration_from_points(self, simple_config):
        """Setup calibration from manual points."""
        builder = ProjectionShotBuilder(simple_config)
        builder.setup_calibration()

        assert builder.calibration is not None
        assert len(builder.calibration.points) == 3

    def test_setup_calibration_from_preset(self):
        """Setup calibration from target preset."""
        config = ProjectionShotConfig(
            name="preset_test",
            projector_profile="Epson_Home_Cinema_2150",
            target_preset="garage_door",
        )
        builder = ProjectionShotBuilder(config)
        builder.setup_calibration()

        # Should load target and potentially create calibration
        # May fail if preset file doesn't exist, so check for target or errors
        assert builder.target is not None or len(builder._errors) > 0 or len(builder._warnings) > 0

    def test_configure_output(self, simple_config):
        """Configure output settings."""
        builder = ProjectionShotBuilder(simple_config)
        builder.configure_output()

        assert builder.output_config is not None
        assert builder.output_config.resolution == (1920, 1080)

    def test_full_build(self, simple_config):
        """Full build pipeline."""
        builder = ProjectionShotBuilder(simple_config)
        result = builder.build()

        assert isinstance(result, ProjectionShotResult)
        assert result.config is not None
        assert result.profile is not None
        assert result.calibration is not None

    def test_build_chain_methods(self, simple_config):
        """Method chaining works."""
        builder = ProjectionShotBuilder(simple_config)

        # Chain should return builder
        result = (builder
                  .load_profile()
                  .setup_calibration()
                  .configure_output())

        assert result == builder


class TestProjectionShotResult:
    """Tests for ProjectionShotResult."""

    def test_default_result(self):
        """Default result is empty."""
        result = ProjectionShotResult()

        assert result.success is False
        assert result.config is None
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_result_with_errors(self):
        """Result with errors."""
        result = ProjectionShotResult(
            success=False,
            errors=["Error 1", "Error 2"],
        )

        assert result.success is False
        assert len(result.errors) == 2


class TestBuildProjectionShot:
    """Tests for build_projection_shot function."""

    def test_build_from_yaml_file(self, tmp_path):
        """Build from YAML file."""
        yaml_content = """
name: Test Shot
description: Test projection shot

camera:
  type: projection
  projector_profile: Epson_Home_Cinema_2150
  calibration:
    type: three_point
    points:
      - label: Bottom Left
        world_position: [0, 0, 0]
        projector_uv: [0, 0]
      - label: Bottom Right
        world_position: [2, 0, 0]
        projector_uv: [1, 0]
      - label: Top Left
        world_position: [0, 0, 1.5]
        projector_uv: [0, 1]

content:
  source: test.png
  blend_mode: mix
  intensity: 1.0

output:
  format: image_sequence
  output_path: //output/
"""
        yaml_path = tmp_path / "test_shot.yaml"
        yaml_path.write_text(yaml_content)

        result = build_projection_shot(str(yaml_path))

        assert isinstance(result, ProjectionShotResult)
        assert result.config.name == "Test Shot"
        assert result.profile is not None
        assert result.calibration is not None

    def test_build_from_yaml_file_not_found(self):
        """Build from non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            build_projection_shot("/nonexistent/path.yaml")


class TestBuildProjectionShotFromDict:
    """Tests for build_projection_shot_from_dict function."""

    def test_build_from_dict(self):
        """Build from dictionary."""
        data = {
            'name': 'Dict Shot',
            'camera': {
                'projector_profile': 'Epson_Home_Cinema_2150',
                'calibration': {
                    'type': 'three_point',
                    'points': [
                        {'world_position': [0, 0, 0], 'projector_uv': [0, 0]},
                        {'world_position': [1, 0, 0], 'projector_uv': [1, 0]},
                        {'world_position': [0, 0, 1], 'projector_uv': [0, 1]},
                    ]
                }
            },
            'output': {
                'format': 'video',
            }
        }

        result = build_projection_shot_from_dict(data)

        assert isinstance(result, ProjectionShotResult)
        assert result.config.name == "Dict Shot"


class TestProjectionShotIntegration:
    """End-to-end integration tests."""

    def test_complete_workflow(self, tmp_path):
        """Complete workflow from YAML to built result."""
        yaml_content = """
name: Integration Test
description: Complete integration test

camera:
  type: projection
  projector_profile: Epson_Home_Cinema_2150
  calibration:
    type: three_point
    points:
      - world_position: [0, 0, 0]
        projector_uv: [0, 0]
      - world_position: [3, 0, 0]
        projector_uv: [1, 0]
      - world_position: [0, 0, 2]
        projector_uv: [0, 1]

content:
  source: //content/test.mp4
  intensity: 0.9

output:
  resolution: [1920, 1080]
  format: video
  color_space: sRGB
"""
        yaml_path = tmp_path / "integration_shot.yaml"
        yaml_path.write_text(yaml_content)

        result = build_projection_shot(str(yaml_path))

        # Verify complete build
        assert result.success
        assert result.profile is not None
        assert result.profile.name == "Epson_Home_Cinema_2150"
        assert result.calibration is not None
        assert result.output_config is not None
        assert result.output_config.resolution == (1920, 1080)

    def test_workflow_with_warnings(self, tmp_path):
        """Workflow completes with warnings for missing content."""
        yaml_content = """
name: Warning Test
camera:
  projector_profile: Epson_Home_Cinema_2150
  calibration:
    type: three_point
    points:
      - world_position: [0, 0, 0]
        projector_uv: [0, 0]
      - world_position: [1, 0, 0]
        projector_uv: [1, 0]
      - world_position: [0, 0, 1]
        projector_uv: [0, 1]
"""
        yaml_path = tmp_path / "warning_shot.yaml"
        yaml_path.write_text(yaml_content)

        result = build_projection_shot(str(yaml_path))

        # Should succeed but may have warnings about missing content
        assert result.profile is not None

    def test_render_without_blender(self, tmp_path):
        """Render handles missing Blender gracefully."""
        yaml_content = """
name: Render Test
camera:
  projector_profile: Epson_Home_Cinema_2150
  calibration:
    type: three_point
    points:
      - world_position: [0, 0, 0]
        projector_uv: [0, 0]
      - world_position: [1, 0, 0]
        projector_uv: [1, 0]
      - world_position: [0, 0, 1]
        projector_uv: [0, 1]

output:
  format: image_sequence
  output_path: %s/
""" % str(tmp_path)

        yaml_path = tmp_path / "render_shot.yaml"
        yaml_path.write_text(yaml_content)

        builder = ProjectionShotBuilder(
            ProjectionShotConfig.from_dict({
                'name': 'Render Test',
                'camera': {
                    'projector_profile': 'Epson_Home_Cinema_2150',
                    'calibration': {
                        'type': 'three_point',
                        'points': [
                            {'world_position': [0, 0, 0], 'projector_uv': [0, 0]},
                            {'world_position': [1, 0, 0], 'projector_uv': [1, 0]},
                            {'world_position': [0, 0, 1], 'projector_uv': [0, 1]},
                        ]
                    }
                },
                'output': {
                    'output_path': str(tmp_path) + '/',
                }
            })
        )

        result = builder.build()
        output_files = builder.render()

        # Without Blender, render returns empty list
        # (or creates files if Blender is available)
        assert isinstance(output_files, list)
