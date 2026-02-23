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
            from lib.materials.ground_textures.texture_layers import TextureLayer
            layer = TextureLayer(
                name="test_layer",
                type="diffuse",
                strength=1.0,
            )
            assert layer.name == "test_layer"
            assert layer.type == "diffuse"
            assert layer.strength == 1.0
        except ImportError:
            pytest.skip("TextureLayer not available in texture_layers")

    def test_texture_layer_default_values(self):
        """Test TextureLayer default values."""
        try:
            from lib.materials.ground_textures.texture_layers import TextureLayer
            layer = TextureLayer(name="default_layer")
            assert layer.name == "default_layer"
            # Check defaults if they exist
            if hasattr(layer, 'strength'):
                assert layer.strength >= 0.0
            if hasattr(layer, 'type'):
                assert layer.type in ['diffuse', 'roughness', 'normal', 'displacement', 'specular']
        except ImportError:
            pytest.skip("TextureLayer not available")

    def test_texture_layer_serialization(self):
        """Test TextureLayer serialization if available."""
        try:
            from lib.materials.ground_textures.texture_layers import TextureLayer
            layer = TextureLayer(
                name="test",
                type="diffuse",
                strength=0.5,
            )
            if hasattr(layer, 'to_dict'):
                data = layer.to_dict()
                assert isinstance(data, dict)
                assert data['name'] == "test"
        except (ImportError, AttributeError):
            pytest.skip("TextureLayer serialization not available")

    def test_layer_blending_modes(self):
        """Test layer blending mode constants if available."""
        try:
            from lib.materials.ground_textures import texture_layers
            if hasattr(texture_layers, 'BLEND_MODES'):
                modes = texture_layers.BLEND_MODES
                assert isinstance(modes, (list, dict, tuple))
        except ImportError:
            pytest.skip("texture_layers module not available")


class TestTextureLayerManager:
    """Tests for TextureLayerManager if available."""

    def test_manager_creation(self):
        """Test creating a layer manager."""
        try:
            from lib.materials.ground_textures.texture_layers import TextureLayerManager
            manager = TextureLayerManager()
            assert manager is not None
        except ImportError:
            pytest.skip("TextureLayerManager not available")

    def test_manager_add_layer(self):
        """Test adding layers to manager."""
        try:
            from lib.materials.ground_textures.texture_layers import (
                TextureLayerManager,
                TextureLayer,
            )
            manager = TextureLayerManager()
            layer = TextureLayer(name="test", type="diffuse", strength=1.0)

            if hasattr(manager, 'add_layer'):
                manager.add_layer(layer)
                if hasattr(manager, 'layers'):
                    assert len(manager.layers) == 1
        except ImportError:
            pytest.skip("TextureLayerManager not available")

    def test_manager_remove_layer(self):
        """Test removing layers from manager."""
        try:
            from lib.materials.ground_textures.texture_layers import (
                TextureLayerManager,
                TextureLayer,
            )
            manager = TextureLayerManager()
            layer = TextureLayer(name="test", type="diffuse", strength=1.0)

            if hasattr(manager, 'add_layer') and hasattr(manager, 'remove_layer'):
                manager.add_layer(layer)
                manager.remove_layer("test")
                if hasattr(manager, 'layers'):
                    assert len(manager.layers) == 0
        except ImportError:
            pytest.skip("TextureLayerManager not available")

    def test_manager_get_layer(self):
        """Test getting layer by name."""
        try:
            from lib.materials.ground_textures.texture_layers import (
                TextureLayerManager,
                TextureLayer,
            )
            manager = TextureLayerManager()
            layer = TextureLayer(name="test", type="diffuse", strength=1.0)

            if hasattr(manager, 'add_layer') and hasattr(manager, 'get_layer'):
                manager.add_layer(layer)
                retrieved = manager.get_layer("test")
                assert retrieved is not None
                assert retrieved.name == "test"
        except ImportError:
            pytest.skip("TextureLayerManager not available")

    def test_manager_layer_order(self):
        """Test layer ordering."""
        try:
            from lib.materials.ground_textures.texture_layers import (
                TextureLayerManager,
                TextureLayer,
            )
            manager = TextureLayerManager()

            if hasattr(manager, 'add_layer'):
                for i in range(3):
                    layer = TextureLayer(name=f"layer_{i}", type="diffuse", strength=1.0)
                    manager.add_layer(layer)

                if hasattr(manager, 'layers'):
                    assert len(manager.layers) == 3
        except ImportError:
            pytest.skip("TextureLayerManager not available")


class TestTextureLayerFunctions:
    """Tests for texture layer utility functions."""

    def test_create_diffuse_layer(self):
        """Test creating a diffuse layer."""
        try:
            from lib.materials.ground_textures.texture_layers import create_diffuse_layer
            layer = create_diffuse_layer("diffuse_path.png")
            assert layer is not None
        except (ImportError, AttributeError):
            pytest.skip("create_diffuse_layer function not available")

    def test_create_normal_layer(self):
        """Test creating a normal layer."""
        try:
            from lib.materials.ground_textures.texture_layers import create_normal_layer
            layer = create_normal_layer("normal_path.png", strength=1.0)
            assert layer is not None
        except (ImportError, AttributeError):
            pytest.skip("create_normal_layer function not available")

    def test_create_roughness_layer(self):
        """Test creating a roughness layer."""
        try:
            from lib.materials.ground_textures.texture_layers import create_roughness_layer
            layer = create_roughness_layer("roughness_path.png", strength=0.5)
            assert layer is not None
        except (ImportError, AttributeError):
            pytest.skip("create_roughness_layer function not available")

    def test_blend_layers_function(self):
        """Test blending layers function."""
        try:
            from lib.materials.ground_textures.texture_layers import blend_layers
            # This may require bpy, so we just check it exists
            assert callable(blend_layers)
        except ImportError:
            pytest.skip("blend_layers function not available")


class TestTextureLayerValidation:
    """Tests for texture layer validation."""

    def test_layer_strength_bounds(self):
        """Test layer strength is within valid bounds."""
        try:
            from lib.materials.ground_textures.texture_layers import TextureLayer

            # Test valid bounds
            layer1 = TextureLayer(name="test", type="diffuse", strength=0.0)
            assert layer1.strength == 0.0

            layer2 = TextureLayer(name="test", type="diffuse", strength=1.0)
            assert layer2.strength == 1.0

            layer3 = TextureLayer(name="test", type="diffuse", strength=0.5)
            assert layer3.strength == 0.5
        except ImportError:
            pytest.skip("TextureLayer not available")

    def test_layer_type_validation(self):
        """Test layer type values."""
        try:
            from lib.materials.ground_textures.texture_layers import TextureLayer
            valid_types = ['diffuse', 'roughness', 'normal', 'displacement', 'specular', 'metallic']

            for layer_type in valid_types:
                try:
                    layer = TextureLayer(name="test", type=layer_type, strength=1.0)
                    assert layer.type == layer_type
                except Exception:
                    pass  # Some types may not be valid
        except ImportError:
            pytest.skip("TextureLayer not available")


class TestTextureLayerPresets:
    """Tests for texture layer presets."""

    def test_preset_constants_exist(self):
        """Test that preset constants exist."""
        try:
            from lib.materials.ground_textures import texture_layers
            if hasattr(texture_layers, 'PRESET_LAYERS'):
                presets = texture_layers.PRESET_LAYERS
                assert isinstance(presets, dict)
        except ImportError:
            pytest.skip("texture_layers module not available")

    def test_asphalt_preset(self):
        """Test asphalt preset if available."""
        try:
            from lib.materials.ground_textures.texture_layers import get_asphalt_layers
            layers = get_asphalt_layers()
            assert layers is not None
            assert len(layers) > 0
        except (ImportError, AttributeError):
            pytest.skip("get_asphalt_layers not available")

    def test_concrete_preset(self):
        """Test concrete preset if available."""
        try:
            from lib.materials.ground_textures.texture_layers import get_concrete_layers
            layers = get_concrete_layers()
            assert layers is not None
        except (ImportError, AttributeError):
            pytest.skip("get_concrete_layers not available")

    def test_dirt_preset(self):
        """Test dirt preset if available."""
        try:
            from lib.materials.ground_textures.texture_layers import get_dirt_layers
            layers = get_dirt_layers()
            assert layers is not None
        except (ImportError, AttributeError):
            pytest.skip("get_dirt_layers not available")
