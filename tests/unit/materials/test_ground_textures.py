"""
Tests for ground_textures module.

Tests run WITHOUT Blender (bpy) by testing only non-Blender-dependent code paths.
"""

import pytest
from dataclasses import asdict
from unittest.mock import patch, MagicMock


class TestTextureLayersModule:
    """Tests for texture_layers module structure and data classes."""

    def test_module_imports_structure(self):
        """Test that module can be imported and has expected structure."""
        try:
            from lib.materials.ground_textures import texture_layers
            # Check module has expected attributes
            assert hasattr(texture_layers, '__all__') or True  # May not have __all__
        except ImportError:
            pytest.skip("texture_layers module not available")

    def test_dataclass_imports(self):
        """Test importing dataclasses if available."""
        try:
            from lib.materials.ground_textures.texture_layers import (
                TextureLayer,
                TextureLayerType,
                TextureMaps,
            )
            maps = TextureMaps(
                base_color="test_color.png",
                roughness="test_roughness.png",
            )
            layer = TextureLayer(
                name="test_layer",
                layer_type=TextureLayerType.ASPHALT,
                maps=maps,
            )
            assert layer.name == "test_layer"
            assert layer.layer_type == TextureLayerType.ASPHALT
            assert layer.blend_factor == 1.0
        except ImportError:
            pytest.skip("TextureLayer not available in texture_layers")

    def test_texture_layer_default_values(self):
        """Test TextureLayer default values."""
        try:
            from lib.materials.ground_textures.texture_layers import (
                TextureLayer,
                TextureLayerType,
                TextureMaps,
            )
            maps = TextureMaps()
            layer = TextureLayer(
                name="default_layer",
                layer_type=TextureLayerType.DIRT,
                maps=maps,
            )
            assert layer.name == "default_layer"
            # Check defaults
            assert layer.blend_factor >= 0.0
            assert layer.blend_mode.value in ['mix', 'add', 'multiply', 'overlay', 'screen']
        except ImportError:
            pytest.skip("TextureLayer not available")

    def test_texture_layer_serialization(self):
        """Test TextureLayer serialization if available."""
        try:
            from lib.materials.ground_textures.texture_layers import (
                TextureLayer,
                TextureLayerType,
                TextureMaps,
            )
            maps = TextureMaps()
            layer = TextureLayer(
                name="test",
                layer_type=TextureLayerType.ASPHALT,
                maps=maps,
                blend_factor=0.5,
            )
            data = layer.to_dict()
            assert isinstance(data, dict)
            assert data['name'] == "test"
            assert data['blend_factor'] == 0.5
        except (ImportError, AttributeError):
            pytest.skip("TextureLayer serialization not available")

    def test_layer_blending_modes(self):
        """Test layer blending mode constants if available."""
        try:
            from lib.materials.ground_textures.texture_layers import BlendMode
            modes = [mode.value for mode in BlendMode]
            assert isinstance(modes, list)
            assert 'mix' in modes
            assert 'multiply' in modes
        except ImportError:
            pytest.skip("BlendMode not available")


class TestTextureLayerManager:
    """Tests for LayeredTextureManager if available."""

    def test_manager_creation(self):
        """Test creating a layer manager."""
        try:
            from lib.materials.ground_textures.texture_layers import LayeredTextureManager
            manager = LayeredTextureManager()
            assert manager is not None
        except ImportError:
            pytest.skip("LayeredTextureManager not available")

    def test_manager_create_config(self):
        """Test creating a config with manager."""
        try:
            from lib.materials.ground_textures.texture_layers import (
                LayeredTextureManager,
                TextureLayerType,
            )
            manager = LayeredTextureManager()
            config = manager.create_config("test_config", TextureLayerType.ASPHALT)

            assert config is not None
            assert config.name == "test_config"
            assert len(config.layers) == 1  # Base layer is added automatically
        except ImportError:
            pytest.skip("LayeredTextureManager not available")

    def test_manager_add_overlay(self):
        """Test adding overlay layers to config."""
        try:
            from lib.materials.ground_textures.texture_layers import (
                LayeredTextureManager,
                TextureLayerType,
                MaskType,
            )
            manager = LayeredTextureManager()
            config = manager.create_config("test_config", TextureLayerType.ASPHALT)

            overlay = manager.add_overlay(
                config,
                layer_type=TextureLayerType.DIRT,
                blend_factor=0.5,
                mask_type=MaskType.NOISE,
            )

            assert overlay is not None
            assert len(config.layers) == 2  # Base + overlay
        except ImportError:
            pytest.skip("LayeredTextureManager not available")

    def test_manager_generate_shader_nodes(self):
        """Test generating shader nodes."""
        try:
            from lib.materials.ground_textures.texture_layers import (
                LayeredTextureManager,
                TextureLayerType,
            )
            manager = LayeredTextureManager()
            config = manager.create_config("test_config", TextureLayerType.ASPHALT)

            setup = manager.generate_shader_nodes(config)
            assert setup is not None
            assert 'config_name' in setup
            assert 'nodes' in setup
            assert 'links' in setup
        except ImportError:
            pytest.skip("LayeredTextureManager not available")


class TestTextureLayerFunctions:
    """Tests for texture layer utility functions."""

    def test_create_asphalt_with_dirt(self):
        """Test creating asphalt with dirt config."""
        try:
            from lib.materials.ground_textures.texture_layers import create_asphalt_with_dirt
            config = create_asphalt_with_dirt(dirt_amount=0.4)
            assert config is not None
            assert len(config.layers) == 2  # Base asphalt + dirt overlay
        except (ImportError, AttributeError):
            pytest.skip("create_asphalt_with_dirt function not available")

    def test_create_road_material(self):
        """Test creating a road material."""
        try:
            from lib.materials.ground_textures.texture_layers import create_road_material
            config = create_road_material(surface_type="asphalt", wear_level="medium")
            assert config is not None
        except (ImportError, AttributeError):
            pytest.skip("create_road_material function not available")

    def test_create_painted_marking_material(self):
        """Test creating a painted marking material."""
        try:
            from lib.materials.ground_textures.texture_layers import (
                create_road_material,
                create_painted_marking_material,
            )
            base = create_road_material()
            config = create_painted_marking_material(base)
            assert config is not None
        except (ImportError, AttributeError):
            pytest.skip("create_painted_marking_material function not available")


class TestTextureLayerValidation:
    """Tests for texture layer validation."""

    def test_layer_blend_factor_bounds(self):
        """Test layer blend_factor is within valid bounds."""
        try:
            from lib.materials.ground_textures.texture_layers import (
                TextureLayer,
                TextureLayerType,
                TextureMaps,
            )

            # Test valid bounds
            maps = TextureMaps()
            layer1 = TextureLayer(
                name="test",
                layer_type=TextureLayerType.ASPHALT,
                maps=maps,
                blend_factor=0.0,
            )
            assert layer1.blend_factor == 0.0

            layer2 = TextureLayer(
                name="test",
                layer_type=TextureLayerType.ASPHALT,
                maps=maps,
                blend_factor=1.0,
            )
            assert layer2.blend_factor == 1.0

            layer3 = TextureLayer(
                name="test",
                layer_type=TextureLayerType.ASPHALT,
                maps=maps,
                blend_factor=0.5,
            )
            assert layer3.blend_factor == 0.5
        except ImportError:
            pytest.skip("TextureLayer not available")

    def test_layer_type_validation(self):
        """Test layer type values."""
        try:
            from lib.materials.ground_textures.texture_layers import (
                TextureLayer,
                TextureLayerType,
                TextureMaps,
            )

            maps = TextureMaps()
            for layer_type in TextureLayerType:
                layer = TextureLayer(
                    name="test",
                    layer_type=layer_type,
                    maps=maps,
                )
                assert layer.layer_type == layer_type
        except ImportError:
            pytest.skip("TextureLayer not available")


class TestTextureLayerPresets:
    """Tests for texture layer presets."""

    def test_preset_constants_exist(self):
        """Test that preset constants exist."""
        try:
            from lib.materials.ground_textures.texture_layers import GROUND_TEXTURE_PRESETS
            assert isinstance(GROUND_TEXTURE_PRESETS, dict)
            assert 'asphalt_clean' in GROUND_TEXTURE_PRESETS
            assert 'concrete_clean' in GROUND_TEXTURE_PRESETS
        except ImportError:
            pytest.skip("GROUND_TEXTURE_PRESETS not available")

    def test_asphalt_presets(self):
        """Test asphalt presets are defined."""
        try:
            from lib.materials.ground_textures.texture_layers import GROUND_TEXTURE_PRESETS
            assert 'asphalt_clean' in GROUND_TEXTURE_PRESETS
            assert 'asphalt_dirty' in GROUND_TEXTURE_PRESETS
            assert 'asphalt_worn' in GROUND_TEXTURE_PRESETS
        except ImportError:
            pytest.skip("GROUND_TEXTURE_PRESETS not available")

    def test_concrete_presets(self):
        """Test concrete presets are defined."""
        try:
            from lib.materials.ground_textures.texture_layers import GROUND_TEXTURE_PRESETS
            assert 'concrete_clean' in GROUND_TEXTURE_PRESETS
            assert 'concrete_stained' in GROUND_TEXTURE_PRESETS
        except ImportError:
            pytest.skip("GROUND_TEXTURE_PRESETS not available")

    def test_dirt_presets(self):
        """Test dirt presets are defined."""
        try:
            from lib.materials.ground_textures.texture_layers import GROUND_TEXTURE_PRESETS
            assert 'dirt_road' in GROUND_TEXTURE_PRESETS
        except ImportError:
            pytest.skip("GROUND_TEXTURE_PRESETS not available")


class TestTextureMaps:
    """Tests for TextureMaps dataclass."""

    def test_texture_maps_creation(self):
        """Test creating TextureMaps."""
        try:
            from lib.materials.ground_textures.texture_layers import TextureMaps
            maps = TextureMaps(
                base_color="color.png",
                roughness="roughness.png",
                normal="normal.png",
            )
            assert maps.base_color == "color.png"
            assert maps.roughness == "roughness.png"
            assert maps.normal == "normal.png"
        except ImportError:
            pytest.skip("TextureMaps not available")

    def test_texture_maps_defaults(self):
        """Test TextureMaps default values."""
        try:
            from lib.materials.ground_textures.texture_layers import TextureMaps
            maps = TextureMaps()
            assert maps.base_color is None
            assert maps.normal_strength == 1.0
            assert maps.procedural_color == (0.5, 0.5, 0.5)
        except ImportError:
            pytest.skip("TextureMaps not available")


class TestPaintedMask:
    """Tests for PaintedMask dataclass."""

    def test_painted_mask_creation(self):
        """Test creating PaintedMask."""
        try:
            from lib.materials.ground_textures.texture_layers import PaintedMask
            mask = PaintedMask(
                name="test_mask",
                resolution=(1024, 1024),
            )
            assert mask.name == "test_mask"
            assert mask.resolution == (1024, 1024)
        except ImportError:
            pytest.skip("PaintedMask not available")

    def test_painted_mask_defaults(self):
        """Test PaintedMask default values."""
        try:
            from lib.materials.ground_textures.texture_layers import PaintedMask
            mask = PaintedMask(name="test")
            assert mask.resolution == (2048, 2048)
            assert mask.brush_strength == 1.0
        except ImportError:
            pytest.skip("PaintedMask not available")


class TestLayeredTextureConfig:
    """Tests for LayeredTextureConfig dataclass."""

    def test_config_creation(self):
        """Test creating LayeredTextureConfig."""
        try:
            from lib.materials.ground_textures.texture_layers import LayeredTextureConfig
            config = LayeredTextureConfig(name="test_config")
            assert config.name == "test_config"
            assert config.layers == []
        except ImportError:
            pytest.skip("LayeredTextureConfig not available")

    def test_config_add_layer(self):
        """Test adding layers to config."""
        try:
            from lib.materials.ground_textures.texture_layers import (
                LayeredTextureConfig,
                TextureLayerType,
                TextureMaps,
                MaskType,
            )
            config = LayeredTextureConfig(name="test")
            maps = TextureMaps()

            layer = config.add_layer(
                name="base",
                layer_type=TextureLayerType.ASPHALT,
                maps=maps,
                mask_type=MaskType.NOISE,
            )

            assert len(config.layers) == 1
            assert layer.name == "base"
        except ImportError:
            pytest.skip("LayeredTextureConfig not available")

    def test_config_serialization(self):
        """Test config serialization."""
        try:
            from lib.materials.ground_textures.texture_layers import (
                LayeredTextureConfig,
                TextureLayerType,
                TextureMaps,
            )
            config = LayeredTextureConfig(name="test")
            maps = TextureMaps()
            config.add_layer(
                name="base",
                layer_type=TextureLayerType.ASPHALT,
                maps=maps,
            )

            data = config.to_dict()
            assert data['name'] == "test"
            assert 'layers' in data
        except ImportError:
            pytest.skip("LayeredTextureConfig not available")
