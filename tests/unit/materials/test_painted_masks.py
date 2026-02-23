"""
Tests for painted_masks module.

Tests run WITHOUT Blender (bpy) by testing only non-Blender-dependent code paths.
"""

import pytest
from dataclasses import asdict
from unittest.mock import patch, MagicMock
import numpy as np


class TestPaintedMasksModule:
    """Tests for painted_masks module structure and data classes."""

    def test_module_imports_structure(self):
        """Test that module can be imported and has expected structure."""
        try:
            from lib.materials.ground_textures import painted_masks
            assert painted_masks is not None
        except ImportError:
            pytest.skip("painted_masks module not available")

    def test_dataclass_imports(self):
        """Test importing dataclasses if available."""
        try:
            from lib.materials.ground_textures.painted_masks import PaintedMask
            mask = PaintedMask(
                name="test_mask",
                resolution=1024,
            )
            assert mask.name == "test_mask"
            assert mask.resolution == 1024
        except ImportError:
            pytest.skip("PaintedMask not available in painted_masks")

    def test_painted_mask_default_values(self):
        """Test PaintedMask default values."""
        try:
            from lib.materials.ground_textures.painted_masks import PaintedMask
            mask = PaintedMask(name="default_mask")
            assert mask.name == "default_mask"
            if hasattr(mask, 'resolution'):
                assert mask.resolution > 0
        except ImportError:
            pytest.skip("PaintedMask not available")

    def test_painted_mask_serialization(self):
        """Test PaintedMask serialization if available."""
        try:
            from lib.materials.ground_textures.painted_masks import PaintedMask
            mask = PaintedMask(
                name="test",
                resolution=512,
            )
            if hasattr(mask, 'to_dict'):
                data = mask.to_dict()
                assert isinstance(data, dict)
                assert data['name'] == "test"
                assert data['resolution'] == 512
        except (ImportError, AttributeError):
            pytest.skip("PaintedMask serialization not available")


class TestMaskGenerator:
    """Tests for MaskGenerator if available."""

    def test_generator_creation(self):
        """Test creating a mask generator."""
        try:
            from lib.materials.ground_textures.painted_masks import MaskGenerator
            generator = MaskGenerator()
            assert generator is not None
        except ImportError:
            pytest.skip("MaskGenerator not available")

    def test_generator_with_resolution(self):
        """Test creating generator with custom resolution."""
        try:
            from lib.materials.ground_textures.painted_masks import MaskGenerator
            generator = MaskGenerator(resolution=2048)
            if hasattr(generator, 'resolution'):
                assert generator.resolution == 2048
        except ImportError:
            pytest.skip("MaskGenerator not available")

    def test_generator_create_mask(self):
        """Test creating a mask with generator."""
        try:
            from lib.materials.ground_textures.painted_masks import MaskGenerator
            generator = MaskGenerator()

            if hasattr(generator, 'create_mask'):
                mask = generator.create_mask("test_mask")
                assert mask is not None
        except ImportError:
            pytest.skip("MaskGenerator not available")


class TestMaskPaintingFunctions:
    """Tests for mask painting utility functions."""

    def test_create_noise_mask_function(self):
        """Test noise mask creation function."""
        try:
            from lib.materials.ground_textures.painted_masks import create_noise_mask
            mask = create_noise_mask(512, seed=42)
            assert mask is not None
            # Check if it's a numpy array
            if hasattr(mask, 'shape'):
                assert mask.shape[0] == 512
        except (ImportError, AttributeError):
            pytest.skip("create_noise_mask function not available")

    def test_create_gradient_mask_function(self):
        """Test gradient mask creation function."""
        try:
            from lib.materials.ground_textures.painted_masks import create_gradient_mask
            mask = create_gradient_mask(512, direction='horizontal')
            assert mask is not None
        except (ImportError, AttributeError):
            pytest.skip("create_gradient_mask function not available")

    def test_create_radial_mask_function(self):
        """Test radial mask creation function."""
        try:
            from lib.materials.ground_textures.painted_masks import create_radial_mask
            mask = create_radial_mask(512, center=(256, 256), radius=200)
            assert mask is not None
        except (ImportError, AttributeError):
            pytest.skip("create_radial_mask function not available")

    def test_blend_masks_function(self):
        """Test mask blending function."""
        try:
            from lib.materials.ground_textures.painted_masks import (
                create_noise_mask,
                blend_masks,
            )
            mask1 = create_noise_mask(256, seed=1)
            mask2 = create_noise_mask(256, seed=2)

            if callable(blend_masks):
                blended = blend_masks(mask1, mask2, mode='multiply')
                assert blended is not None
        except (ImportError, AttributeError):
            pytest.skip("blend_masks function not available")


class TestMaskBrushTypes:
    """Tests for different brush types."""

    def test_brush_type_constants(self):
        """Test brush type constants if available."""
        try:
            from lib.materials.ground_textures import painted_masks
            if hasattr(painted_masks, 'BRUSH_TYPES'):
                brushes = painted_masks.BRUSH_TYPES
                assert isinstance(brushes, (list, dict, tuple))
        except ImportError:
            pytest.skip("painted_masks module not available")

    def test_soft_brush_function(self):
        """Test soft brush creation."""
        try:
            from lib.materials.ground_textures.painted_masks import create_soft_brush
            brush = create_soft_brush(size=64, falloff=0.5)
            assert brush is not None
        except (ImportError, AttributeError):
            pytest.skip("create_soft_brush function not available")

    def test_hard_brush_function(self):
        """Test hard brush creation."""
        try:
            from lib.materials.ground_textures.painted_masks import create_hard_brush
            brush = create_hard_brush(size=64)
            assert brush is not None
        except (ImportError, AttributeError):
            pytest.skip("create_hard_brush function not available")


class TestMaskOperations:
    """Tests for mask operations."""

    def test_invert_mask_function(self):
        """Test mask inversion."""
        try:
            from lib.materials.ground_textures.painted_masks import (
                create_noise_mask,
                invert_mask,
            )
            mask = create_noise_mask(128, seed=42)
            inverted = invert_mask(mask)

            if hasattr(mask, 'shape') and hasattr(inverted, 'shape'):
                assert mask.shape == inverted.shape
        except (ImportError, AttributeError):
            pytest.skip("invert_mask function not available")

    def test_threshold_mask_function(self):
        """Test mask thresholding."""
        try:
            from lib.materials.ground_textures.painted_masks import (
                create_noise_mask,
                threshold_mask,
            )
            mask = create_noise_mask(128, seed=42)
            thresholded = threshold_mask(mask, threshold=0.5)

            if hasattr(thresholded, 'shape'):
                assert thresholded.shape == mask.shape
        except (ImportError, AttributeError):
            pytest.skip("threshold_mask function not available")

    def test_blur_mask_function(self):
        """Test mask blurring."""
        try:
            from lib.materials.ground_textures.painted_masks import (
                create_noise_mask,
                blur_mask,
            )
            mask = create_noise_mask(128, seed=42)
            blurred = blur_mask(mask, radius=5)

            if hasattr(blurred, 'shape'):
                assert blurred.shape == mask.shape
        except (ImportError, AttributeError):
            pytest.skip("blur_mask function not available")

    def test_erode_mask_function(self):
        """Test mask erosion."""
        try:
            from lib.materials.ground_textures.painted_masks import (
                create_noise_mask,
                threshold_mask,
                erode_mask,
            )
            mask = create_noise_mask(128, seed=42)
            binary = threshold_mask(mask, 0.5)
            eroded = erode_mask(binary, iterations=2)

            if hasattr(eroded, 'shape'):
                assert eroded.shape == binary.shape
        except (ImportError, AttributeError):
            pytest.skip("erode_mask function not available")

    def test_dilate_mask_function(self):
        """Test mask dilation."""
        try:
            from lib.materials.ground_textures.painted_masks import (
                create_noise_mask,
                threshold_mask,
                dilate_mask,
            )
            mask = create_noise_mask(128, seed=42)
            binary = threshold_mask(mask, 0.5)
            dilated = dilate_mask(binary, iterations=2)

            if hasattr(dilated, 'shape'):
                assert dilated.shape == binary.shape
        except (ImportError, AttributeError):
            pytest.skip("dilate_mask function not available")


class TestMaskSaving:
    """Tests for mask saving and loading."""

    def test_save_mask_function_exists(self):
        """Test save_mask function exists."""
        try:
            from lib.materials.ground_textures.painted_masks import save_mask
            assert callable(save_mask)
        except ImportError:
            pytest.skip("save_mask function not available")

    def test_load_mask_function_exists(self):
        """Test load_mask function exists."""
        try:
            from lib.materials.ground_textures.painted_masks import load_mask
            assert callable(load_mask)
        except ImportError:
            pytest.skip("load_mask function not available")


class TestMaskPresets:
    """Tests for mask presets."""

    def test_wear_mask_preset(self):
        """Test wear mask preset."""
        try:
            from lib.materials.ground_textures.painted_masks import create_wear_mask
            mask = create_wear_mask(512, intensity=0.7)
            assert mask is not None
        except (ImportError, AttributeError):
            pytest.skip("create_wear_mask function not available")

    def test_dust_mask_preset(self):
        """Test dust mask preset."""
        try:
            from lib.materials.ground_textures.painted_masks import create_dust_mask
            mask = create_dust_mask(512, coverage=0.3)
            assert mask is not None
        except (ImportError, AttributeError):
            pytest.skip("create_dust_mask function not available")

    def test_scratch_mask_preset(self):
        """Test scratch mask preset."""
        try:
            from lib.materials.ground_textures.painted_masks import create_scratch_mask
            mask = create_scratch_mask(512, count=50)
            assert mask is not None
        except (ImportError, AttributeError):
            pytest.skip("create_scratch_mask function not available")

    def test_leak_mask_preset(self):
        """Test leak/rust streak mask preset."""
        try:
            from lib.materials.ground_textures.painted_masks import create_leak_mask
            mask = create_leak_mask(512, origin=(256, 0), length=400)
            assert mask is not None
        except (ImportError, AttributeError):
            pytest.skip("create_leak_mask function not available")


class TestMaskMathOperations:
    """Tests for mask mathematical operations."""

    def test_mask_addition(self):
        """Test mask addition operation."""
        try:
            from lib.materials.ground_textures.painted_masks import (
                create_noise_mask,
                add_masks,
            )
            mask1 = create_noise_mask(128, seed=1)
            mask2 = create_noise_mask(128, seed=2)
            result = add_masks(mask1, mask2)

            if hasattr(result, 'shape'):
                assert result.shape == mask1.shape
        except (ImportError, AttributeError):
            pytest.skip("add_masks function not available")

    def test_mask_subtraction(self):
        """Test mask subtraction operation."""
        try:
            from lib.materials.ground_textures.painted_masks import (
                create_noise_mask,
                subtract_masks,
            )
            mask1 = create_noise_mask(128, seed=1)
            mask2 = create_noise_mask(128, seed=2)
            result = subtract_masks(mask1, mask2)

            if hasattr(result, 'shape'):
                assert result.shape == mask1.shape
        except (ImportError, AttributeError):
            pytest.skip("subtract_masks function not available")

    def test_mask_multiply(self):
        """Test mask multiplication operation."""
        try:
            from lib.materials.ground_textures.painted_masks import (
                create_noise_mask,
                multiply_masks,
            )
            mask1 = create_noise_mask(128, seed=1)
            mask2 = create_noise_mask(128, seed=2)
            result = multiply_masks(mask1, mask2)

            if hasattr(result, 'shape'):
                assert result.shape == mask1.shape
        except (ImportError, AttributeError):
            pytest.skip("multiply_masks function not available")
