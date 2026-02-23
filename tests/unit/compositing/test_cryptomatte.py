"""
Tests for lib/compositing/cryptomatte.py

Comprehensive tests for cryptomatte system without Blender (bpy).
"""

import pytest
import tempfile
import os
import json

from lib.compositing.cryptomatte import (
    CryptomatteLayer,
    MatteType,
    CryptomatteConfig,
    CryptomattePass,
    MatteData,
    CRYPTOMATTE_PRESETS,
    CryptomatteManager,
    create_cryptomatte_config,
    extract_matte_from_manifest,
    hash_to_rgb,
)


class TestCryptomatteLayer:
    """Tests for CryptomatteLayer enum."""

    def test_layer_types_exist(self):
        """Test that expected layer types exist."""
        assert hasattr(CryptomatteLayer, 'OBJECT')
        assert hasattr(CryptomatteLayer, 'MATERIAL')
        assert hasattr(CryptomatteLayer, 'ASSET')
        assert hasattr(CryptomatteLayer, 'COLLECTION')

    def test_layer_values(self):
        """Test layer enum values."""
        assert CryptomatteLayer.OBJECT.value == "object"
        assert CryptomatteLayer.MATERIAL.value == "material"
        assert CryptomatteLayer.ASSET.value == "asset"


class TestMatteType:
    """Tests for MatteType enum."""

    def test_matte_types_exist(self):
        """Test that expected matte types exist."""
        assert hasattr(MatteType, 'OBJECT')
        assert hasattr(MatteType, 'MATERIAL')
        assert hasattr(MatteType, 'COLLECTION')
        assert hasattr(MatteType, 'CUSTOM')


class TestCryptomatteConfig:
    """Tests for CryptomatteConfig dataclass."""

    def test_create_config(self):
        """Test creating config."""
        config = CryptomatteConfig(
            config_id="test",
            name="Test Config",
        )
        assert config.config_id == "test"
        assert config.name == "Test Config"

    def test_config_defaults(self):
        """Test config default values."""
        config = CryptomatteConfig()
        assert config.layers == ["object", "material"]
        assert config.depth == 6
        assert config.manifest is True
        assert config.anti_aliasing == 4

    def test_config_to_dict(self):
        """Test config serialization."""
        config = CryptomatteConfig(
            config_id="test",
            name="Test",
            depth=8,
        )
        data = config.to_dict()
        assert data["config_id"] == "test"
        assert data["name"] == "Test"
        assert data["depth"] == 8

    def test_config_from_dict(self):
        """Test config deserialization."""
        data = {
            "config_id": "loaded",
            "name": "Loaded Config",
            "layers": ["object"],
            "depth": 12,
            "manifest": False,
        }
        config = CryptomatteConfig.from_dict(data)
        assert config.config_id == "loaded"
        assert config.name == "Loaded Config"
        assert config.layers == ["object"]
        assert config.depth == 12
        assert config.manifest is False


class TestCryptomattePass:
    """Tests for CryptomattePass dataclass."""

    def test_create_pass(self):
        """Test creating cryptomatte pass."""
        cryp_pass = CryptomattePass(
            pass_id="pass_001",
            layer_type="object",
            pass_name="Object Cryptomatte",
        )
        assert cryp_pass.pass_id == "pass_001"
        assert cryp_pass.layer_type == "object"

    def test_pass_to_dict(self):
        """Test pass serialization."""
        cryp_pass = CryptomattePass(
            pass_id="test",
            layer_type="material",
            objects=["Cube", "Sphere"],
        )
        data = cryp_pass.to_dict()
        assert data["pass_id"] == "test"
        assert data["layer_type"] == "material"
        assert "Cube" in data["objects"]


class TestMatteData:
    """Tests for MatteData dataclass."""

    def test_create_matte_data(self):
        """Test creating matte data."""
        matte = MatteData(
            matte_id="matte_001",
            name="Cube",
            matte_type="object",
            hash_value="abc123",
        )
        assert matte.matte_id == "matte_001"
        assert matte.name == "Cube"
        assert matte.hash_value == "abc123"

    def test_matte_data_to_dict(self):
        """Test matte data serialization."""
        matte = MatteData(
            matte_id="test",
            name="Test",
            color=(1.0, 0.5, 0.0),
        )
        data = matte.to_dict()
        assert data["matte_id"] == "test"
        assert data["color"] == [1.0, 0.5, 0.0]


class TestCryptomattePresets:
    """Tests for cryptomatte presets."""

    def test_presets_exist(self):
        """Test that presets exist."""
        assert isinstance(CRYPTOMATTE_PRESETS, dict)
        assert len(CRYPTOMATTE_PRESETS) > 0

    def test_standard_preset(self):
        """Test standard preset."""
        assert "standard" in CRYPTOMATTE_PRESETS
        preset = CRYPTOMATTE_PRESETS["standard"]
        assert "object" in preset["layers"] or "material" in preset["layers"]

    def test_production_preset(self):
        """Test production preset."""
        assert "production" in CRYPTOMATTE_PRESETS
        preset = CRYPTOMATTE_PRESETS["production"]
        assert preset["depth"] >= 6

    def test_vfx_preset(self):
        """Test VFX preset has higher depth."""
        assert "vfx" in CRYPTOMATTE_PRESETS
        preset = CRYPTOMATTE_PRESETS["vfx"]
        assert preset["depth"] >= 6


class TestCryptomatteManager:
    """Tests for CryptomatteManager class."""

    def test_create_manager(self):
        """Test creating manager."""
        manager = CryptomatteManager()
        assert manager is not None
        assert isinstance(manager.configs, dict)
        assert isinstance(manager.passes, dict)

    def test_manager_loads_presets(self):
        """Test that manager loads presets."""
        manager = CryptomatteManager()
        # Should have loaded presets as configs
        assert len(manager.configs) > 0

    def test_create_config(self):
        """Test creating config via manager."""
        manager = CryptomatteManager()
        config = manager.create_config("my_config", name="My Config")
        assert config.config_id == "my_config"
        assert config.name == "My Config"
        assert "my_config" in manager.configs

    def test_create_config_with_preset(self):
        """Test creating config with preset."""
        manager = CryptomatteManager()
        config = manager.create_config("custom", preset="production")
        assert config.config_id == "custom"
        # Should inherit from production preset
        assert config.depth >= 6

    def test_get_config(self):
        """Test getting config by ID."""
        manager = CryptomatteManager()
        manager.create_config("test_config")
        config = manager.get_config("test_config")
        assert config is not None
        assert config.config_id == "test_config"

    def test_get_config_not_found(self):
        """Test getting non-existent config."""
        manager = CryptomatteManager()
        config = manager.get_config("nonexistent")
        assert config is None

    def test_list_configs(self):
        """Test listing configs."""
        manager = CryptomatteManager()
        manager.create_config("cfg1")
        manager.create_config("cfg2")
        configs = manager.list_configs()
        assert len(configs) >= 2

    def test_create_pass(self):
        """Test creating cryptomatte pass."""
        manager = CryptomatteManager()
        cryp_pass = manager.create_pass("pass1", "object")
        assert cryp_pass.pass_id == "pass1"
        assert cryp_pass.layer_type == "object"

    def test_get_pass(self):
        """Test getting pass by ID."""
        manager = CryptomatteManager()
        manager.create_pass("test_pass", "material")
        cryp_pass = manager.get_pass("test_pass")
        assert cryp_pass is not None

    def test_setup_render_passes(self):
        """Test setting up render passes."""
        manager = CryptomatteManager()
        config = manager.create_config("test", layers=["object", "material"])
        passes = manager.setup_render_passes(config, "/output")
        assert len(passes) == 2

    def test_parse_manifest(self):
        """Test parsing manifest file."""
        manager = CryptomatteManager()

        # Create temp manifest
        manifest_data = {
            "entries": {
                "abc123": {"name": "Cube", "type": "object"},
                "def456": {"name": "Sphere", "type": "object"},
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(manifest_data, f)
            temp_path = f.name

        try:
            mattes = manager.parse_manifest(temp_path)
            assert len(mattes) == 2
            assert "Cube" in mattes
            assert "Sphere" in mattes
        finally:
            os.unlink(temp_path)

    def test_parse_manifest_invalid(self):
        """Test parsing invalid manifest."""
        manager = CryptomatteManager()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json")
            temp_path = f.name

        try:
            mattes = manager.parse_manifest(temp_path)
            assert mattes == {}
        finally:
            os.unlink(temp_path)

    def test_extract_matte(self):
        """Test extracting matte."""
        manager = CryptomatteManager()

        # Create temp manifest
        manifest_data = {
            "entries": {
                "abc123": {"name": "Cube", "type": "object"},
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(manifest_data, f)
            manifest_path = f.name

        try:
            matte = manager.extract_matte("Cube", "/render.exr", manifest_path)
            assert matte is not None
            assert matte.name == "Cube"
        finally:
            os.unlink(manifest_path)

    def test_extract_matte_not_found(self):
        """Test extracting non-existent matte."""
        manager = CryptomatteManager()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"entries": {}}, f)
            manifest_path = f.name

        try:
            matte = manager.extract_matte("NonExistent", "/render.exr", manifest_path)
            assert matte is None
        finally:
            os.unlink(manifest_path)

    def test_get_matte_by_hash(self):
        """Test getting matte by hash."""
        manager = CryptomatteManager()

        manifest_data = {
            "entries": {
                "hash123": {"name": "Test", "type": "object"},
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(manifest_data, f)
            manifest_path = f.name

        try:
            manager.parse_manifest(manifest_path)
            matte = manager.get_matte_by_hash("hash123")
            assert matte is not None
            assert matte.name == "Test"
        finally:
            os.unlink(manifest_path)

    def test_get_mattes_by_type(self):
        """Test getting mattes by type."""
        manager = CryptomatteManager()

        manifest_data = {
            "entries": {
                "h1": {"name": "Obj1", "type": "object"},
                "h2": {"name": "Obj2", "type": "object"},
                "h3": {"name": "Mat1", "type": "material"},
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(manifest_data, f)
            manifest_path = f.name

        try:
            manager.parse_manifest(manifest_path)
            objects = manager.get_mattes_by_type("object")
            assert len(objects) == 2

            materials = manager.get_mattes_by_type("material")
            assert len(materials) == 1
        finally:
            os.unlink(manifest_path)

    def test_get_mattes_by_prefix(self):
        """Test getting mattes by name prefix."""
        manager = CryptomatteManager()

        manifest_data = {
            "entries": {
                "h1": {"name": "Char_Hero", "type": "object"},
                "h2": {"name": "Char_Villain", "type": "object"},
                "h3": {"name": "Prop_Table", "type": "object"},
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(manifest_data, f)
            manifest_path = f.name

        try:
            manager.parse_manifest(manifest_path)
            chars = manager.get_mattes_by_prefix("Char_")
            assert len(chars) == 2
        finally:
            os.unlink(manifest_path)

    def test_generate_compositor_setup(self):
        """Test generating compositor setup."""
        manager = CryptomatteManager()
        config = manager.create_config("test", layers=["object"])
        setup = manager.generate_compositor_setup(config)
        assert "nodes" in setup
        assert "links" in setup

    def test_get_statistics(self):
        """Test getting manager statistics."""
        manager = CryptomatteManager()
        stats = manager.get_statistics()
        assert "total_configs" in stats
        assert "total_passes" in stats
        assert "total_mattes" in stats


class TestCreateCryptomatteConfig:
    """Tests for create_cryptomatte_config helper."""

    def test_create_config_basic(self):
        """Test basic config creation."""
        config = create_cryptomatte_config("Test Config")
        assert config is not None
        assert "test_config" in config.config_id

    def test_create_config_with_layers(self):
        """Test config with custom layers."""
        config = create_cryptomatte_config(
            "Test",
            layers=["object", "material", "asset"],
        )
        assert "object" in config.layers

    def test_create_config_with_depth(self):
        """Test config with custom depth."""
        config = create_cryptomatte_config("Test", depth=12)
        assert config.depth == 12


class TestExtractMatteFromManifest:
    """Tests for extract_matte_from_manifest helper."""

    def test_extract_matte(self):
        """Test extracting matte from manifest."""
        manifest_data = {
            "entries": {
                "hash1": {"name": "TestObject", "type": "object"},
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(manifest_data, f)
            manifest_path = f.name

        try:
            matte = extract_matte_from_manifest(manifest_path, "TestObject")
            assert matte is not None
            assert matte.name == "TestObject"
        finally:
            os.unlink(manifest_path)

    def test_extract_matte_not_found(self):
        """Test extracting non-existent matte."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"entries": {}}, f)
            manifest_path = f.name

        try:
            matte = extract_matte_from_manifest(manifest_path, "NonExistent")
            assert matte is None
        finally:
            os.unlink(manifest_path)


class TestHashToRgb:
    """Tests for hash_to_rgb function."""

    def test_hash_to_rgb_basic(self):
        """Test basic hash to RGB conversion."""
        rgb = hash_to_rgb("ffffff")
        assert len(rgb) == 3
        assert all(0 <= v <= 1 for v in rgb)

    def test_hash_to_rgb_black(self):
        """Test black hash."""
        rgb = hash_to_rgb("000000")
        assert rgb == (0.0, 0.0, 0.0)

    def test_hash_to_rgb_white(self):
        """Test white hash."""
        rgb = hash_to_rgb("ffffff")
        # Should be close to white (may have rounding)
        assert all(v > 0.9 for v in rgb)

    def test_hash_to_rgb_invalid(self):
        """Test invalid hash returns gray."""
        rgb = hash_to_rgb("invalid!")
        assert rgb == (0.5, 0.5, 0.5)


class TestCryptomatteEdgeCases:
    """Tests for edge cases."""

    def test_empty_layers_list(self):
        """Test config with empty layers."""
        config = CryptomatteConfig(layers=[])
        assert config.layers == []

    def test_high_depth(self):
        """Test config with high depth."""
        config = CryptomatteConfig(depth=24)
        assert config.depth == 24

    def test_manifest_missing_entries(self):
        """Test manifest without entries key."""
        manager = CryptomatteManager()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)
            temp_path = f.name

        try:
            mattes = manager.parse_manifest(temp_path)
            assert mattes == {}
        finally:
            os.unlink(temp_path)

    def test_extract_mattes_batch(self):
        """Test extracting multiple mattes."""
        manager = CryptomatteManager()

        manifest_data = {
            "entries": {
                "h1": {"name": "A", "type": "object"},
                "h2": {"name": "B", "type": "object"},
                "h3": {"name": "C", "type": "object"},
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(manifest_data, f)
            manifest_path = f.name

        try:
            mattes = manager.extract_mattes(["A", "B"], "/render.exr", manifest_path)
            assert len(mattes) == 2
            assert "A" in mattes
            assert "B" in mattes
        finally:
            os.unlink(manifest_path)
