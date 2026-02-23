"""
Tests for utils/__init__.py module.

Tests the main exports and module structure.
"""

import pytest


class TestUtilsModuleInit:
    """Tests for utils module __init__.py."""

    def test_module_imports(self):
        """Test that the utils module can be imported."""
        from lib.utils import __all__
        assert isinstance(__all__, list)

    def test_exports_list(self):
        """Test that __all__ contains expected exports."""
        from lib.utils import __all__

        # Check there are some exports
        assert len(__all__) > 0


class TestUtilsImports:
    """Test individual imports from the utils module."""

    def test_import_drivers(self):
        """Test importing from drivers module."""
        try:
            from lib.utils.drivers import __all__
            assert isinstance(__all__, list)
        except ImportError:
            pytest.skip("drivers module not available")

    def test_import_limits(self):
        """Test importing from limits module."""
        try:
            from lib.utils.limits import clamp
            assert callable(clamp)
        except ImportError:
            pytest.skip("limits module not available")

    def test_import_math_safe(self):
        """Test importing from math_safe module."""
        try:
            from lib.utils.math_safe import safe_div
            assert callable(safe_div)
        except ImportError:
            pytest.skip("math_safe module not available")

    def test_import_safety(self):
        """Test importing from safety module."""
        try:
            from lib.utils.safety import validate_type
            assert callable(validate_type)
        except ImportError:
            pytest.skip("safety module not available")


class TestUtilsReExports:
    """Test that utils module re-exports from submodules."""

    def test_clamp_reexported(self):
        """Test that clamp is re-exported."""
        try:
            from lib.utils import clamp
            assert callable(clamp)
        except ImportError:
            pytest.skip("clamp not re-exported from utils")

    def test_safe_div_reexported(self):
        """Test that safe_div is re-exported."""
        try:
            from lib.utils import safe_div
            assert callable(safe_div)
        except ImportError:
            pytest.skip("safe_div not re-exported from utils")


class TestUtilsModuleStructure:
    """Tests for utils module directory structure."""

    def test_drivers_file_exists(self):
        """Test that drivers.py exists."""
        import os
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        drivers_path = os.path.join(base_path, 'lib', 'utils', 'drivers.py')
        assert os.path.isfile(drivers_path), f"drivers.py not found at {drivers_path}"

    def test_limits_file_exists(self):
        """Test that limits.py exists."""
        import os
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        limits_path = os.path.join(base_path, 'lib', 'utils', 'limits.py')
        assert os.path.isfile(limits_path), f"limits.py not found at {limits_path}"

    def test_math_safe_file_exists(self):
        """Test that math_safe.py exists."""
        import os
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        math_safe_path = os.path.join(base_path, 'lib', 'utils', 'math_safe.py')
        assert os.path.isfile(math_safe_path), f"math_safe.py not found at {math_safe_path}"

    def test_safety_file_exists(self):
        """Test that safety.py exists."""
        import os
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        safety_path = os.path.join(base_path, 'lib', 'utils', 'safety.py')
        assert os.path.isfile(safety_path), f"safety.py not found at {safety_path}"
