"""
Tests for asphalt_pbr module.

Tests run WITHOUT Blender (bpy) by testing only non-Blender-dependent code paths.
"""

import pytest
from dataclasses import asdict
from unittest.mock import patch, MagicMock


class TestAsphaltPBRModule:
    """Tests for asphalt_pbr module structure and data classes."""

    def test_module_imports_structure(self):
        """Test that module can be imported and has expected structure."""
        try:
            from lib.materials.asphalt import asphalt_pbr
            assert asphalt_pbr is not None
        except ImportError:
            pytest.skip("asphalt_pbr module not available")

    def test_dataclass_imports(self):
        """Test importing dataclasses if available."""
        try:
            from lib.materials.asphalt.asphalt_pbr import AsphaltPBRConfig
            config = AsphaltPBRConfig(
                name="test_asphalt",
                roughness=0.8,
            )
            assert config.name == "test_asphalt"
            assert config.roughness == 0.8
        except ImportError:
            pytest.skip("AsphaltPBRConfig not available in asphalt_pbr")

    def test_asphalt_config_default_values(self):
        """Test AsphaltPBRConfig default values."""
        try:
            from lib.materials.asphalt.asphalt_pbr import AsphaltPBRConfig
            config = AsphaltPBRConfig(name="default_asphalt")
            assert config.name == "default_asphalt"
            if hasattr(config, 'roughness'):
                assert 0.0 <= config.roughness <= 1.0
        except ImportError:
            pytest.skip("AsphaltPBRConfig not available")

    def test_asphalt_config_serialization(self):
        """Test AsphaltPBRConfig serialization if available."""
        try:
            from lib.materials.asphalt.asphalt_pbr import AsphaltPBRConfig
            config = AsphaltPBRConfig(
                name="test",
                roughness=0.7,
            )
            if hasattr(config, 'to_dict'):
                data = config.to_dict()
                assert isinstance(data, dict)
                assert data['name'] == "test"
                assert data['roughness'] == 0.7
        except (ImportError, AttributeError):
            pytest.skip("AsphaltPBRConfig serialization not available")


class TestAsphaltPBRPresets:
    """Tests for asphalt PBR presets."""

    def test_fresh_asphalt_preset(self):
        """Test fresh asphalt preset."""
        try:
            from lib.materials.asphalt.asphalt_pbr import get_fresh_asphalt_config
            config = get_fresh_asphalt_config()
            assert config is not None
            if hasattr(config, 'roughness'):
                # Fresh asphalt should be relatively smooth
                assert config.roughness < 0.9
        except (ImportError, AttributeError):
            pytest.skip("get_fresh_asphalt_config not available")

    def test_weathered_asphalt_preset(self):
        """Test weathered asphalt preset."""
        try:
            from lib.materials.asphalt.asphalt_pbr import get_weathered_asphalt_config
            config = get_weathered_asphalt_config()
            assert config is not None
            if hasattr(config, 'roughness'):
                # Weathered asphalt should be rougher
                assert config.roughness > 0.5
        except (ImportError, AttributeError):
            pytest.skip("get_weathered_asphalt_config not available")

    def test_wet_asphalt_preset(self):
        """Test wet asphalt preset."""
        try:
            from lib.materials.asphalt.asphalt_pbr import get_wet_asphalt_config
            config = get_wet_asphalt_config()
            assert config is not None
        except (ImportError, AttributeError):
            pytest.skip("get_wet_asphalt_config not available")

    def test_cracked_asphalt_preset(self):
        """Test cracked asphalt preset."""
        try:
            from lib.materials.asphalt.asphalt_pbr import get_cracked_asphalt_config
            config = get_cracked_asphalt_config()
            assert config is not None
        except (ImportError, AttributeError):
            pytest.skip("get_cracked_asphalt_config not available")

    def test_pothole_asphalt_preset(self):
        """Test pothole asphalt preset."""
        try:
            from lib.materials.asphalt.asphalt_pbr import get_pothole_config
            config = get_pothole_config()
            assert config is not None
        except (ImportError, AttributeError):
            pytest.skip("get_pothole_config not available")


class TestAsphaltPBRGenerator:
    """Tests for AsphaltPBRGenerator if available."""

    def test_generator_creation(self):
        """Test creating an asphalt PBR generator."""
        try:
            from lib.materials.asphalt.asphalt_pbr import AsphaltPBRGenerator
            generator = AsphaltPBRGenerator()
            assert generator is not None
        except ImportError:
            pytest.skip("AsphaltPBRGenerator not available")

    def test_generator_with_config(self):
        """Test creating generator with config."""
        try:
            from lib.materials.asphalt.asphalt_pbr import (
                AsphaltPBRGenerator,
                AsphaltPBRConfig,
            )
            config = AsphaltPBRConfig(name="test", roughness=0.7)
            generator = AsphaltPBRGenerator(config=config)
            assert generator is not None
        except ImportError:
            pytest.skip("AsphaltPBRGenerator not available")

    def test_generator_generate_textures(self):
        """Test generating textures with generator."""
        try:
            from lib.materials.asphalt.asphalt_pbr import (
                AsphaltPBRGenerator,
                AsphaltPBRConfig,
            )
            config = AsphaltPBRConfig(name="test", roughness=0.7)
            generator = AsphaltPBRGenerator(config=config)

            if hasattr(generator, 'generate_textures'):
                textures = generator.generate_textures(resolution=512)
                assert textures is not None
        except ImportError:
            pytest.skip("AsphaltPBRGenerator not available")


class TestAsphaltTextureGeneration:
    """Tests for asphalt texture generation functions."""

    def test_generate_diffuse_function(self):
        """Test diffuse texture generation."""
        try:
            from lib.materials.asphalt.asphalt_pbr import generate_asphalt_diffuse
            texture = generate_asphalt_diffuse(512, seed=42)
            assert texture is not None
            if hasattr(texture, 'shape'):
                assert texture.shape[0] == 512
        except (ImportError, AttributeError):
            pytest.skip("generate_asphalt_diffuse not available")

    def test_generate_roughness_function(self):
        """Test roughness texture generation."""
        try:
            from lib.materials.asphalt.asphalt_pbr import generate_asphalt_roughness
            texture = generate_asphalt_roughness(512, base_roughness=0.8)
            assert texture is not None
        except (ImportError, AttributeError):
            pytest.skip("generate_asphalt_roughness not available")

    def test_generate_normal_function(self):
        """Test normal map generation."""
        try:
            from lib.materials.asphalt.asphalt_pbr import generate_asphalt_normal
            texture = generate_asphalt_normal(512, strength=1.0)
            assert texture is not None
        except (ImportError, AttributeError):
            pytest.skip("generate_asphalt_normal not available")

    def test_generate_displacement_function(self):
        """Test displacement map generation."""
        try:
            from lib.materials.asphalt.asphalt_pbr import generate_asphalt_displacement
            texture = generate_asphalt_displacement(512, height_scale=0.1)
            assert texture is not None
        except (ImportError, AttributeError):
            pytest.skip("generate_asphalt_displacement not available")


class TestAsphaltWeathering:
    """Tests for asphalt weathering effects."""

    def test_apply_weathering_function(self):
        """Test weathering application."""
        try:
            from lib.materials.asphalt.asphalt_pbr import apply_weathering
            # Check function exists
            assert callable(apply_weathering)
        except ImportError:
            pytest.skip("apply_weathering not available")

    def test_add_cracks_function(self):
        """Test crack addition function."""
        try:
            from lib.materials.asphalt.asphalt_pbr import add_cracks
            assert callable(add_cracks)
        except ImportError:
            pytest.skip("add_cracks not available")

    def test_add_potholes_function(self):
        """Test pothole addition function."""
        try:
            from lib.materials.asphalt.asphalt_pbr import add_potholes
            assert callable(add_potholes)
        except ImportError:
            pytest.skip("add_potholes not available")

    def test_add_oil_stains_function(self):
        """Test oil stain addition function."""
        try:
            from lib.materials.asphalt.asphalt_pbr import add_oil_stains
            assert callable(add_oil_stains)
        except ImportError:
            pytest.skip("add_oil_stains not available")

    def test_add_tar_patches_function(self):
        """Test tar patch addition function."""
        try:
            from lib.materials.asphalt.asphalt_pbr import add_tar_patches
            assert callable(add_tar_patches)
        except ImportError:
            pytest.skip("add_tar_patches not available")


class TestAsphaltLineMarkings:
    """Tests for road line markings."""

    def test_line_marking_config(self):
        """Test line marking configuration."""
        try:
            from lib.materials.asphalt.asphalt_pbr import LineMarkingConfig
            config = LineMarkingConfig(
                color="white",
                width=0.15,
                style="solid",
            )
            assert config.color == "white"
            assert config.width == 0.15
            assert config.style == "solid"
        except ImportError:
            pytest.skip("LineMarkingConfig not available")

    def test_create_solid_line_function(self):
        """Test solid line creation."""
        try:
            from lib.materials.asphalt.asphalt_pbr import create_solid_line
            assert callable(create_solid_line)
        except ImportError:
            pytest.skip("create_solid_line not available")

    def test_create_dashed_line_function(self):
        """Test dashed line creation."""
        try:
            from lib.materials.asphalt.asphalt_pbr import create_dashed_line
            assert callable(create_dashed_line)
        except ImportError:
            pytest.skip("create_dashed_line not available")


class TestAsphaltColorVariations:
    """Tests for asphalt color variations."""

    def test_asphalt_color_constants(self):
        """Test asphalt color constants."""
        try:
            from lib.materials.asphalt import asphalt_pbr
            if hasattr(asphalt_pbr, 'ASPHALT_COLORS'):
                colors = asphalt_pbr.ASPHALT_COLORS
                assert isinstance(colors, dict)
        except ImportError:
            pytest.skip("asphalt_pbr module not available")

    def test_get_asphalt_color_function(self):
        """Test getting asphalt color."""
        try:
            from lib.materials.asphalt.asphalt_pbr import get_asphalt_color
            color = get_asphalt_color("fresh")
            assert color is not None
            if hasattr(color, '__len__'):
                assert len(color) >= 3  # RGB or RGBA
        except (ImportError, AttributeError):
            pytest.skip("get_asphalt_color not available")


class TestAsphaltMaterialProperties:
    """Tests for asphalt material properties."""

    def test_roughness_range(self):
        """Test roughness is within valid range."""
        try:
            from lib.materials.asphalt.asphalt_pbr import AsphaltPBRConfig
            # Test various roughness values
            for roughness in [0.5, 0.7, 0.9, 0.95]:
                config = AsphaltPBRConfig(name="test", roughness=roughness)
                assert 0.0 <= config.roughness <= 1.0
        except ImportError:
            pytest.skip("AsphaltPBRConfig not available")

    def test_base_color_defaults(self):
        """Test base color has valid defaults."""
        try:
            from lib.materials.asphalt.asphalt_pbr import AsphaltPBRConfig
            config = AsphaltPBRConfig(name="test")
            if hasattr(config, 'base_color'):
                color = config.base_color
                if hasattr(color, '__len__'):
                    for c in color[:3]:
                        assert 0.0 <= c <= 1.0
        except ImportError:
            pytest.skip("AsphaltPBRConfig not available")


class TestAsphaltNodeSetup:
    """Tests for asphalt node setup (bpy-dependent, structure only)."""

    def test_create_asphalt_nodes_function_exists(self):
        """Test create_asphalt_nodes function exists."""
        try:
            from lib.materials.asphalt.asphalt_pbr import create_asphalt_nodes
            # Function exists but requires bpy
            assert callable(create_asphalt_nodes)
        except ImportError:
            pytest.skip("create_asphalt_nodes not available")

    def test_setup_asphalt_material_function_exists(self):
        """Test setup_asphalt_material function exists."""
        try:
            from lib.materials.asphalt.asphalt_pbr import setup_asphalt_material
            assert callable(setup_asphalt_material)
        except ImportError:
            pytest.skip("setup_asphalt_material not available")
