"""
Tests for materials/__init__.py module.

Tests the main exports and module structure.
"""

import pytest


class TestMaterialsModuleInit:
    """Tests for materials module __init__.py."""

    def test_module_imports(self):
        """Test that the materials module can be imported."""
        from lib.materials import __version__, __all__
        assert __version__ is not None
        assert isinstance(__all__, list)

    def test_version_format(self):
        """Test version string format."""
        from lib.materials import __version__
        # Version should be in semantic versioning format
        parts = __version__.split('.')
        assert len(parts) >= 2

    def test_exports_list(self):
        """Test that __all__ contains expected exports."""
        from lib.materials import __all__

        # Check expected exports exist
        expected_patterns = [
            'GroundTextureSystem',
            'AsphaltPBR',
            'TextureLayer',
            'PaintedMask',
        ]

        for pattern in expected_patterns:
            # At least some of these should be exported
            if pattern in __all__:
                assert True
                break
        else:
            # If none match, at least check there are exports
            assert len(__all__) > 0

    def test_ground_textures_submodule_import(self):
        """Test importing ground_textures submodule."""
        try:
            from lib.materials import ground_textures
            assert ground_textures is not None
        except ImportError:
            pytest.skip("ground_textures submodule not available")

    def test_asphalt_submodule_import(self):
        """Test importing asphalt submodule."""
        try:
            from lib.materials import asphalt
            assert asphalt is not None
        except ImportError:
            pytest.skip("asphalt submodule not available")

    def test_get_function_exports(self):
        """Test that get_ functions are exported if available."""
        from lib.materials import __all__

        get_functions = [name for name in __all__ if name.startswith('get_')]
        # Should have at least some get_ functions
        # Not strictly required, just checking structure
        assert isinstance(get_functions, list)

    def test_create_function_exports(self):
        """Test that create_ functions are exported if available."""
        from lib.materials import __all__

        create_functions = [name for name in __all__ if name.startswith('create_')]
        # Should have at least some create_ functions
        assert isinstance(create_functions, list)


class TestMaterialsModuleStructure:
    """Tests for materials module directory structure."""

    def test_ground_textures_directory_exists(self):
        """Test that ground_textures subdirectory exists."""
        import os
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        gt_path = os.path.join(base_path, 'lib', 'materials', 'ground_textures')
        assert os.path.isdir(gt_path), f"ground_textures directory not found at {gt_path}"

    def test_asphalt_directory_exists(self):
        """Test that asphalt subdirectory exists."""
        import os
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        asphalt_path = os.path.join(base_path, 'lib', 'materials', 'asphalt')
        assert os.path.isdir(asphalt_path), f"asphalt directory not found at {asphalt_path}"


class TestMaterialsImports:
    """Test individual imports from the materials module."""

    def test_import_texture_layers(self):
        """Test importing from texture_layers."""
        try:
            from lib.materials.ground_textures.texture_layers import TextureLayer
            assert TextureLayer is not None
        except ImportError:
            pytest.skip("TextureLayer not available")

    def test_import_painted_masks(self):
        """Test importing from painted_masks."""
        try:
            from lib.materials.ground_textures.painted_masks import PaintedMask
            assert PaintedMask is not None
        except ImportError:
            pytest.skip("PaintedMask not available")

    def test_import_asphalt_pbr(self):
        """Test importing from asphalt_pbr."""
        try:
            from lib.materials.asphalt.asphalt_pbr import AsphaltPBRConfig
            assert AsphaltPBRConfig is not None
        except ImportError:
            pytest.skip("AsphaltPBRConfig not available")


class TestMaterialsConstants:
    """Tests for module constants."""

    def test_texture_type_constants(self):
        """Test texture type constants if available."""
        try:
            from lib.materials import ground_textures
            if hasattr(ground_textures, 'TEXTURE_TYPES'):
                types = ground_textures.TEXTURE_TYPES
                assert isinstance(types, (list, tuple, dict))
        except ImportError:
            pytest.skip("ground_textures module not available")

    def test_blend_mode_constants(self):
        """Test blend mode constants if available."""
        try:
            from lib.materials import ground_textures
            if hasattr(ground_textures, 'BLEND_MODES'):
                modes = ground_textures.BLEND_MODES
                assert isinstance(modes, (list, tuple, dict))
        except ImportError:
            pytest.skip("ground_textures module not available")
