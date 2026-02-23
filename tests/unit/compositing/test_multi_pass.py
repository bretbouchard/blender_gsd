"""
Tests for lib/compositing/multi_pass.py

Comprehensive tests for multi-pass render pipeline without Blender (bpy).
"""

import pytest
import tempfile
import os
import json

from lib.compositing.multi_pass import (
    PassType,
    PassCategory,
    OutputFormat,
    RenderPass,
    PassConfig,
    MultiPassSetup,
    STANDARD_PASSES,
    BEAUTY_PASSES,
    UTILITY_PASSES,
    DATA_PASSES,
    EXR_COMPRESSION_OPTIONS,
    EXR_DEPTH_OPTIONS,
    MultiPassManager,
    create_pass_config,
    create_standard_setup,
)


class TestPassType:
    """Tests for PassType enum."""

    def test_pass_types_exist(self):
        """Test that expected pass types exist."""
        assert hasattr(PassType, 'BEAUTY')
        assert hasattr(PassType, 'DIFFUSE')
        assert hasattr(PassType, 'GLOSSY')
        assert hasattr(PassType, 'NORMAL')
        assert hasattr(PassType, 'Z_DEPTH')
        assert hasattr(PassType, 'VECTOR')
        assert hasattr(PassType, 'CRYPTO')

    def test_pass_type_values(self):
        """Test pass type enum values."""
        assert PassType.BEAUTY.value == "beauty"
        assert PassType.DIFFUSE.value == "diffuse"
        assert PassType.NORMAL.value == "normal"


class TestPassCategory:
    """Tests for PassCategory enum."""

    def test_categories_exist(self):
        """Test that expected categories exist."""
        assert hasattr(PassCategory, 'BEAUTY')
        assert hasattr(PassCategory, 'LIGHTING')
        assert hasattr(PassCategory, 'SHADING')
        assert hasattr(PassCategory, 'GEOMETRY')
        assert hasattr(PassCategory, 'UTILITY')
        assert hasattr(PassCategory, 'DATA')
        assert hasattr(PassCategory, 'CRYPTO')


class TestOutputFormat:
    """Tests for OutputFormat enum."""

    def test_formats_exist(self):
        """Test that expected formats exist."""
        assert hasattr(OutputFormat, 'EXR')
        assert hasattr(OutputFormat, 'PNG')
        assert hasattr(OutputFormat, 'TIFF')
        assert hasattr(OutputFormat, 'HDR')

    def test_format_values(self):
        """Test format enum values."""
        assert OutputFormat.EXR.value == "exr"
        assert OutputFormat.PNG.value == "png"


class TestRenderPass:
    """Tests for RenderPass dataclass."""

    def test_create_render_pass(self):
        """Test creating render pass."""
        render_pass = RenderPass(
            pass_id="test_pass",
            name="Test Pass",
            pass_type="beauty",
        )
        assert render_pass.pass_id == "test_pass"
        assert render_pass.name == "Test Pass"
        assert render_pass.pass_type == "beauty"

    def test_render_pass_defaults(self):
        """Test render pass defaults."""
        render_pass = RenderPass()
        assert render_pass.enabled is True
        assert render_pass.channels == ["RGB"]
        assert render_pass.pass_type == "beauty"

    def test_render_pass_to_dict(self):
        """Test render pass serialization."""
        render_pass = RenderPass(
            pass_id="test",
            name="Test",
            pass_type="normal",
            channels=["XYZ"],
        )
        data = render_pass.to_dict()
        assert data["pass_id"] == "test"
        assert data["name"] == "Test"
        assert data["pass_type"] == "normal"
        assert data["channels"] == ["XYZ"]

    def test_render_pass_from_dict(self):
        """Test render pass deserialization."""
        data = {
            "pass_id": "loaded",
            "name": "Loaded Pass",
            "pass_type": "data",
            "channels": ["Z"],
            "enabled": False,
        }
        render_pass = RenderPass.from_dict(data)
        assert render_pass.pass_id == "loaded"
        assert render_pass.name == "Loaded Pass"
        assert render_pass.pass_type == "data"
        assert render_pass.enabled is False


class TestPassConfig:
    """Tests for PassConfig dataclass."""

    def test_create_config(self):
        """Test creating pass config."""
        config = PassConfig(
            config_id="test",
            name="Test Config",
        )
        assert config.config_id == "test"
        assert config.name == "Test Config"

    def test_config_defaults(self):
        """Test config defaults."""
        config = PassConfig()
        assert config.passes == ["combined"]
        assert config.output_format == "exr"
        assert config.exr_compression == "zip"
        assert config.exr_depth == "32"
        assert config.multi_layer is True

    def test_config_to_dict(self):
        """Test config serialization."""
        config = PassConfig(
            config_id="test",
            name="Test",
            passes=["combined", "normal"],
            exr_compression="dwaa",
        )
        data = config.to_dict()
        assert data["config_id"] == "test"
        assert data["passes"] == ["combined", "normal"]
        assert data["exr_compression"] == "dwaa"

    def test_config_from_dict(self):
        """Test config deserialization."""
        data = {
            "config_id": "loaded",
            "name": "Loaded",
            "passes": ["combined", "z_depth"],
            "output_format": "png",
            "exr_depth": "16",
        }
        config = PassConfig.from_dict(data)
        assert config.config_id == "loaded"
        assert config.passes == ["combined", "z_depth"]
        assert config.output_format == "png"
        assert config.exr_depth == "16"


class TestMultiPassSetup:
    """Tests for MultiPassSetup dataclass."""

    def test_create_setup(self):
        """Test creating setup."""
        setup = MultiPassSetup(
            setup_id="test_setup",
            name="Test Setup",
        )
        assert setup.setup_id == "test_setup"
        assert setup.name == "Test Setup"

    def test_setup_defaults(self):
        """Test setup defaults."""
        setup = MultiPassSetup()
        assert setup.render_passes == []
        assert setup.frame_padding == 4
        assert setup.view_layers == ["ViewLayer"]

    def test_setup_to_dict(self):
        """Test setup serialization."""
        config = PassConfig(config_id="cfg", name="Config")
        setup = MultiPassSetup(
            setup_id="test",
            name="Test",
            pass_config=config,
            output_path="/renders",
        )
        data = setup.to_dict()
        assert data["setup_id"] == "test"
        assert data["output_path"] == "/renders"
        assert data["pass_config"]["config_id"] == "cfg"


class TestStandardPasses:
    """Tests for standard pass definitions."""

    def test_standard_passes_exist(self):
        """Test that standard passes exist."""
        assert isinstance(STANDARD_PASSES, dict)
        assert len(STANDARD_PASSES) > 0

    def test_combined_pass(self):
        """Test combined pass definition."""
        assert "combined" in STANDARD_PASSES
        combined = STANDARD_PASSES["combined"]
        assert combined["type"] == "beauty"
        assert combined["category"] == "beauty"

    def test_diffuse_passes(self):
        """Test diffuse pass definitions."""
        assert "diffuse_direct" in STANDARD_PASSES
        assert "diffuse_indirect" in STANDARD_PASSES
        assert "diffuse_color" in STANDARD_PASSES

    def test_beauty_passes_list(self):
        """Test beauty passes list."""
        assert isinstance(BEAUTY_PASSES, list)
        assert "combined" in BEAUTY_PASSES
        assert "emission" in BEAUTY_PASSES

    def test_utility_passes_exist(self):
        """Test utility passes exist."""
        assert isinstance(UTILITY_PASSES, dict)
        assert "normal" in UTILITY_PASSES
        assert "z_depth" in UTILITY_PASSES
        assert "vector" in UTILITY_PASSES

    def test_data_passes_list(self):
        """Test data passes list."""
        assert isinstance(DATA_PASSES, list)
        assert "normal" in DATA_PASSES
        assert "z_depth" in DATA_PASSES


class TestEXROptions:
    """Tests for EXR options."""

    def test_compression_options_exist(self):
        """Test compression options exist."""
        assert isinstance(EXR_COMPRESSION_OPTIONS, dict)
        assert "zip" in EXR_COMPRESSION_OPTIONS
        assert "dwaa" in EXR_COMPRESSION_OPTIONS

    def test_depth_options_exist(self):
        """Test depth options exist."""
        assert isinstance(EXR_DEPTH_OPTIONS, dict)
        assert "16" in EXR_DEPTH_OPTIONS
        assert "32" in EXR_DEPTH_OPTIONS


class TestMultiPassManager:
    """Tests for MultiPassManager class."""

    def test_create_manager(self):
        """Test creating manager."""
        manager = MultiPassManager()
        assert manager is not None
        assert isinstance(manager.configs, dict)
        assert isinstance(manager.setups, dict)

    def test_manager_loads_standard_passes(self):
        """Test that manager loads standard passes."""
        manager = MultiPassManager()
        assert len(manager.render_passes) > 0
        assert "combined" in manager.render_passes

    def test_create_config(self):
        """Test creating config via manager."""
        manager = MultiPassManager()
        config = manager.create_config("my_config", name="My Config")
        assert config.config_id == "my_config"
        assert config.name == "My Config"
        assert "my_config" in manager.configs

    def test_create_config_with_passes(self):
        """Test creating config with passes."""
        manager = MultiPassManager()
        config = manager.create_config(
            "custom",
            passes=["combined", "normal", "z_depth"],
        )
        assert config.passes == ["combined", "normal", "z_depth"]

    def test_get_config(self):
        """Test getting config by ID."""
        manager = MultiPassManager()
        manager.create_config("test_config")
        config = manager.get_config("test_config")
        assert config is not None
        assert config.config_id == "test_config"

    def test_get_config_not_found(self):
        """Test getting non-existent config."""
        manager = MultiPassManager()
        config = manager.get_config("nonexistent")
        assert config is None

    def test_list_configs(self):
        """Test listing configs."""
        manager = MultiPassManager()
        manager.create_config("cfg1")
        manager.create_config("cfg2")
        configs = manager.list_configs()
        assert len(configs) >= 2

    def test_create_setup(self):
        """Test creating multi-pass setup."""
        manager = MultiPassManager()
        config = manager.create_config("test", passes=["combined", "normal"])
        setup = manager.create_setup(config, "/output/renders")
        assert setup is not None
        assert setup.output_path == "/output/renders"
        assert setup.pass_config == config

    def test_create_setup_creates_render_passes(self):
        """Test that setup creation creates render passes."""
        manager = MultiPassManager()
        config = manager.create_config("test", passes=["combined", "normal"])
        setup = manager.create_setup(config, "/output")
        assert len(setup.render_passes) == 2

    def test_get_setup(self):
        """Test getting setup by ID."""
        manager = MultiPassManager()
        config = manager.create_config("test")
        manager.create_setup(config, "/output")
        setup = manager.get_setup("test_setup")
        assert setup is not None

    def test_list_setups(self):
        """Test listing setups."""
        manager = MultiPassManager()
        # Need two different configs since setup_id is based on config_id
        config1 = manager.create_config("cfg1")
        config2 = manager.create_config("cfg2")
        manager.create_setup(config1, "/out1")
        manager.create_setup(config2, "/out2")
        setups = manager.list_setups()
        assert len(setups) >= 2

    def test_get_pass(self):
        """Test getting render pass by ID."""
        manager = MultiPassManager()
        render_pass = manager.get_pass("combined")
        assert render_pass is not None
        assert render_pass.name == "Combined"

    def test_get_pass_not_found(self):
        """Test getting non-existent pass."""
        manager = MultiPassManager()
        render_pass = manager.get_pass("nonexistent")
        assert render_pass is None

    def test_list_passes(self):
        """Test listing passes."""
        manager = MultiPassManager()
        passes = manager.list_passes()
        assert len(passes) > 0

    def test_list_passes_by_category(self):
        """Test listing passes by category."""
        manager = MultiPassManager()
        beauty_passes = manager.list_passes(category="beauty")
        for p in beauty_passes:
            assert p.category == "beauty"

    def test_list_passes_by_type(self):
        """Test listing passes by type."""
        manager = MultiPassManager()
        normal_passes = manager.list_passes(pass_type="normal")
        for p in normal_passes:
            assert p.pass_type == "normal"

    def test_get_beauty_passes(self):
        """Test getting beauty passes."""
        manager = MultiPassManager()
        passes = manager.get_beauty_passes()
        assert len(passes) > 0

    def test_get_utility_passes(self):
        """Test getting utility passes."""
        manager = MultiPassManager()
        passes = manager.get_utility_passes()
        assert len(passes) > 0

    def test_get_data_passes(self):
        """Test getting data passes."""
        manager = MultiPassManager()
        passes = manager.get_data_passes()
        assert len(passes) > 0

    def test_generate_exr_config(self):
        """Test generating EXR config."""
        manager = MultiPassManager()
        config = manager.create_config("test", passes=["combined", "normal"])
        exr_config = manager.generate_exr_config(config)
        assert "format" in exr_config
        assert "compression" in exr_config
        assert "passes" in exr_config

    def test_generate_exr_config_to_file(self):
        """Test generating EXR config to file."""
        manager = MultiPassManager()
        config = manager.create_config("test", passes=["combined"])

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            manager.generate_exr_config(config, temp_path)
            assert os.path.exists(temp_path)

            with open(temp_path, 'r') as f:
                data = json.load(f)
            assert "format" in data
        finally:
            os.unlink(temp_path)

    def test_generate_compositor_setup(self):
        """Test generating compositor setup."""
        manager = MultiPassManager()
        config = manager.create_config("test", passes=["combined"])
        setup = manager.create_setup(config, "/output")

        compositor = manager.generate_compositor_setup(setup)
        assert "nodes" in compositor
        assert "links" in compositor

    def test_get_pass_statistics(self):
        """Test getting pass statistics."""
        manager = MultiPassManager()
        stats = manager.get_pass_statistics()
        assert "total_passes" in stats
        assert "by_category" in stats
        assert "by_type" in stats

    def test_get_statistics(self):
        """Test getting manager statistics."""
        manager = MultiPassManager()
        stats = manager.get_statistics()
        assert "total_configs" in stats
        assert "total_setups" in stats
        assert "pass_stats" in stats


class TestCreatePassConfig:
    """Tests for create_pass_config helper."""

    def test_create_config_basic(self):
        """Test basic config creation."""
        config = create_pass_config("Test Config")
        assert config is not None
        assert "test_config" in config.config_id

    def test_create_config_with_passes(self):
        """Test config with custom passes."""
        config = create_pass_config(
            "Test",
            passes=["combined", "normal", "z_depth"],
        )
        assert "combined" in config.passes
        assert "normal" in config.passes


class TestCreateStandardSetup:
    """Tests for create_standard_setup helper."""

    def test_create_beauty_setup(self):
        """Test creating beauty setup."""
        setup = create_standard_setup("beauty", "/output")
        assert setup is not None
        assert len(setup.render_passes) >= 1

    def test_create_production_setup(self):
        """Test creating production setup."""
        setup = create_standard_setup("production", "/output")
        assert setup is not None
        # Production includes beauty + utility passes
        assert len(setup.render_passes) > 1

    def test_create_vfx_setup(self):
        """Test creating VFX setup."""
        setup = create_standard_setup("vfx", "/output")
        assert setup is not None
        # VFX includes all passes
        assert len(setup.render_passes) > 5

    def test_create_minimal_setup(self):
        """Test creating minimal setup."""
        setup = create_standard_setup("minimal", "/output")
        assert setup is not None
        assert len(setup.render_passes) == 3  # combined, normal, z_depth

    def test_create_unknown_setup(self):
        """Test creating unknown preset returns None."""
        setup = create_standard_setup("unknown", "/output")
        assert setup is None


class TestMultiPassEdgeCases:
    """Tests for edge cases."""

    def test_empty_passes_list(self):
        """Test config with empty passes."""
        config = PassConfig(passes=[])
        assert config.passes == []

    def test_setup_with_no_config(self):
        """Test setup with no config."""
        setup = MultiPassSetup(setup_id="test")
        assert setup.pass_config is None

    def test_separate_files_config(self):
        """Test separate files configuration."""
        config = PassConfig(separate_files=True)
        assert config.separate_files is True

    def test_single_layer_config(self):
        """Test single-layer EXR configuration."""
        config = PassConfig(multi_layer=False)
        assert config.multi_layer is False

    def test_16bit_depth(self):
        """Test 16-bit depth configuration."""
        config = PassConfig(exr_depth="16")
        assert config.exr_depth == "16"

    def test_setup_with_multiple_view_layers(self):
        """Test setup with multiple view layers."""
        config = PassConfig(config_id="test")
        setup = MultiPassSetup(
            setup_id="test",
            pass_config=config,
            view_layers=["ViewLayer1", "ViewLayer2"],
        )
        assert len(setup.view_layers) == 2
