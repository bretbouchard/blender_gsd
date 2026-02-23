"""
Tests for drivers module.

Tests run WITHOUT Blender (bpy) by testing only non-Blender-dependent code paths.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestDriversModule:
    """Tests for drivers module structure."""

    def test_module_imports(self):
        """Test that the drivers module can be imported."""
        from lib.utils import drivers
        assert drivers is not None

    def test_module_exports_functions(self):
        """Test module exports expected functions."""
        from lib.utils import drivers
        assert hasattr(drivers, 'add_safe_driver')
        assert hasattr(drivers, 'remove_driver')
        assert hasattr(drivers, 'get_drivers')
        assert hasattr(drivers, 'repair_drivers')
        assert hasattr(drivers, 'validate_driver_expression')
        assert hasattr(drivers, 'DriverBuilder')


class TestDataClasses:
    """Tests for driver data classes."""

    def test_driver_variable_creation(self):
        """Test creating a DriverVariable."""
        from lib.utils.drivers import DriverVariable
        var = DriverVariable(
            name="distance",
            target_object="Vehicle",
            data_path="location[0]"
        )
        assert var.name == "distance"
        assert var.target_object == "Vehicle"
        assert var.data_path == "location[0]"
        assert var.transform_space == 'WORLD_SPACE'

    def test_driver_info_creation(self):
        """Test creating a DriverInfo."""
        from lib.utils.drivers import DriverInfo
        info = DriverInfo(
            object_name="Wheel",
            data_path="rotation_euler",
            array_index=1,
            expression="distance / radius",
            variables={"distance": ("Vehicle", "location[0]")}
        )
        assert info.object_name == "Wheel"
        assert info.data_path == "rotation_euler"
        assert info.array_index == 1
        assert info.expression == "distance / radius"


class TestDriverBuilder:
    """Tests for the DriverBuilder fluent API."""

    def test_builder_creation(self):
        """Test creating a DriverBuilder."""
        from lib.utils.drivers import DriverBuilder
        builder = DriverBuilder(None, "location", 0)
        assert builder.data_path == "location"
        assert builder.array_index == 0
        assert builder.expression == "0"

    def test_builder_variable(self):
        """Test adding variable via builder."""
        from lib.utils.drivers import DriverBuilder
        builder = DriverBuilder(None, "location", 0)
        result = builder.variable("distance", None, "location[0]")
        assert result is builder  # Fluent API
        assert "distance" in builder.variables

    def test_builder_average(self):
        """Test setting driver type to AVERAGE."""
        from lib.utils.drivers import DriverBuilder
        builder = DriverBuilder(None, "location", 0)
        result = builder.average()
        assert result is builder
        assert builder.driver_type == 'AVERAGE'

    def test_builder_summation(self):
        """Test setting driver type to SUM."""
        from lib.utils.drivers import DriverBuilder
        builder = DriverBuilder(None, "location", 0)
        result = builder.summation()
        assert result is builder
        assert builder.driver_type == 'SUM'

    def test_builder_transform_channel(self):
        """Test adding transform channel variable."""
        from lib.utils.drivers import DriverBuilder
        builder = DriverBuilder(None, "location", 0)
        result = builder.transform_channel("pos", None, 'LOC_X')
        assert result is builder
        assert "pos" in builder.variables


class TestDriverValidation:
    """Tests for driver validation functions."""

    def test_validate_expression_valid(self):
        """Test validating a valid expression."""
        from lib.utils.drivers import validate_driver_expression
        is_valid, error = validate_driver_expression("var * 2 + 1")
        assert is_valid is True
        assert error is None

    def test_validate_expression_empty(self):
        """Test validating an empty expression."""
        from lib.utils.drivers import validate_driver_expression
        is_valid, error = validate_driver_expression("")
        assert is_valid is False
        assert error == "Empty expression"

    def test_validate_expression_whitespace_only(self):
        """Test validating whitespace-only expression."""
        from lib.utils.drivers import validate_driver_expression
        is_valid, error = validate_driver_expression("   ")
        assert is_valid is False
        assert error == "Empty expression"

    def test_validate_expression_unbalanced_parens_open(self):
        """Test validating expression with unbalanced open parens."""
        from lib.utils.drivers import validate_driver_expression
        is_valid, error = validate_driver_expression("(var + 1")
        assert is_valid is False
        assert error == "Unbalanced parentheses"

    def test_validate_expression_unbalanced_parens_close(self):
        """Test validating expression with unbalanced close parens."""
        from lib.utils.drivers import validate_driver_expression
        is_valid, error = validate_driver_expression("var + 1)")
        assert is_valid is False
        assert error == "Unbalanced parentheses"

    def test_validate_expression_complex_valid(self):
        """Test validating complex valid expression."""
        from lib.utils.drivers import validate_driver_expression
        is_valid, error = validate_driver_expression("sin(var) * cos(var) + 0.5")
        assert is_valid is True
        assert error is None


class TestDriverUtilities:
    """Tests for driver utility functions."""

    def test_fix_driver_expression_no_change(self):
        """Test fixing expression with no renames."""
        from lib.utils.drivers import fix_driver_expression
        result = fix_driver_expression("var * 2", {})
        assert result == "var * 2"

    def test_fix_driver_expression_with_rename(self):
        """Test fixing expression with renames."""
        from lib.utils.drivers import fix_driver_expression
        result = fix_driver_expression(
            "old_name * 2",
            {"old_name": "new_name"}
        )
        assert result == "new_name * 2"


class TestDriverFunctionsNoBlender:
    """Tests for driver functions that handle no-Blender gracefully."""

    def test_add_safe_driver_no_blender(self):
        """Test add_safe_driver when Blender not available."""
        from lib.utils.drivers import add_safe_driver, HAS_BLENDER
        if HAS_BLENDER:
            pytest.skip("Blender is available, skipping no-Blender test")
        result = add_safe_driver(None, "location", 0)
        assert result is None

    def test_get_drivers_no_blender(self):
        """Test get_drivers when Blender not available."""
        from lib.utils.drivers import get_drivers, HAS_BLENDER
        if HAS_BLENDER:
            pytest.skip("Blender is available, skipping no-Blender test")
        result = get_drivers(None)
        assert result == []

    def test_find_drivers_with_object_no_blender(self):
        """Test find_drivers_with_object when Blender not available."""
        from lib.utils.drivers import find_drivers_with_object, HAS_BLENDER
        if HAS_BLENDER:
            pytest.skip("Blender is available, skipping no-Blender test")
        result = find_drivers_with_object("SomeObject")
        assert result == []

    def test_find_drivers_with_expression_no_blender(self):
        """Test find_drivers_with_expression when Blender not available."""
        from lib.utils.drivers import find_drivers_with_expression, HAS_BLENDER
        if HAS_BLENDER:
            pytest.skip("Blender is available, skipping no-Blender test")
        result = find_drivers_with_expression(".*")
        assert result == []

    def test_repair_drivers_no_blender(self):
        """Test repair_drivers when Blender not available."""
        from lib.utils.drivers import repair_drivers, HAS_BLENDER
        if HAS_BLENDER:
            pytest.skip("Blender is available, skipping no-Blender test")
        result = repair_drivers(None)
        assert result == []

    def test_remove_driver_no_blender(self):
        """Test remove_driver when Blender not available."""
        from lib.utils.drivers import remove_driver, HAS_BLENDER
        if HAS_BLENDER:
            pytest.skip("Blender is available, skipping no-Blender test")
        result = remove_driver(None, "location")
        assert result is False

    def test_validate_all_drivers_no_blender(self):
        """Test validate_all_drivers when Blender not available."""
        from lib.utils.drivers import validate_all_drivers, HAS_BLENDER
        if HAS_BLENDER:
            pytest.skip("Blender is available, skipping no-Blender test")
        result = validate_all_drivers()
        assert result == {}


class TestCommonDriverPatterns:
    """Tests for common driver pattern functions."""

    def test_create_wheel_rotation_driver_no_blender(self):
        """Test create_wheel_rotation_driver when Blender not available."""
        from lib.utils.drivers import create_wheel_rotation_driver, HAS_BLENDER
        if HAS_BLENDER:
            pytest.skip("Blender is available, skipping no-Blender test")
        result = create_wheel_rotation_driver(None, None, 0.35, 'Y')
        assert result is None

    def test_create_ik_influence_driver_no_blender(self):
        """Test create_ik_influence_driver when Blender not available."""
        from lib.utils.drivers import create_ik_influence_driver, HAS_BLENDER
        if HAS_BLENDER:
            pytest.skip("Blender is available, skipping no-Blender test")
        result = create_ik_influence_driver(None, "bone", "property")
        assert result is None

    def test_create_visibility_driver_no_blender(self):
        """Test create_visibility_driver when Blender not available."""
        from lib.utils.drivers import create_visibility_driver, HAS_BLENDER
        if HAS_BLENDER:
            pytest.skip("Blender is available, skipping no-Blender test")
        # This one uses DriverBuilder which also returns None without Blender
        result = create_visibility_driver(None, None, "property")
        assert result is None
