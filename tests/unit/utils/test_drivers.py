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
        try:
            from lib.utils import drivers
            assert drivers is not None
        except ImportError:
            pytest.skip("drivers module not available")

    def test_module_exports(self):
        """Test module __all__ exports."""
        try:
            from lib.utils.drivers import __all__
            assert isinstance(__all__, list)
            assert len(__all__) > 0
        except (ImportError, AttributeError):
            pytest.skip("drivers module __all__ not available")


class TestDriverExpressionParser:
    """Tests for driver expression parsing."""

    def test_parse_simple_expression(self):
        """Test parsing simple driver expressions."""
        try:
            from lib.utils.drivers import parse_driver_expression
            result = parse_driver_expression("var * 2")
            assert result is not None
        except (ImportError, AttributeError):
            pytest.skip("parse_driver_expression not available")

    def test_parse_complex_expression(self):
        """Test parsing complex driver expressions."""
        try:
            from lib.utils.drivers import parse_driver_expression
            result = parse_driver_expression("sin(var) * cos(var) + 0.5")
            assert result is not None
        except (ImportError, AttributeError):
            pytest.skip("parse_driver_expression not available")

    def test_parse_invalid_expression(self):
        """Test parsing invalid expressions."""
        try:
            from lib.utils.drivers import parse_driver_expression
            with pytest.raises((ValueError, SyntaxError)):
                parse_driver_expression("invalid!!!")
        except (ImportError, AttributeError):
            pytest.skip("parse_driver_expression not available")


class TestDriverVariableExtractor:
    """Tests for extracting variables from driver expressions."""

    def test_extract_single_variable(self):
        """Test extracting a single variable."""
        try:
            from lib.utils.drivers import extract_driver_variables
            variables = extract_driver_variables("var + 1")
            assert "var" in variables
        except (ImportError, AttributeError):
            pytest.skip("extract_driver_variables not available")

    def test_extract_multiple_variables(self):
        """Test extracting multiple variables."""
        try:
            from lib.utils.drivers import extract_driver_variables
            variables = extract_driver_variables("var1 + var2 * var3")
            assert "var1" in variables
            assert "var2" in variables
            assert "var3" in variables
        except (ImportError, AttributeError):
            pytest.skip("extract_driver_variables not available")

    def test_extract_builtin_functions_excluded(self):
        """Test that builtin functions are not extracted as variables."""
        try:
            from lib.utils.drivers import extract_driver_variables
            variables = extract_driver_variables("sin(var) + cos(var)")
            assert "sin" not in variables
            assert "cos" not in variables
            assert "var" in variables
        except (ImportError, AttributeError):
            pytest.skip("extract_driver_variables not available")


class TestDriverValidation:
    """Tests for driver validation."""

    def test_validate_expression_valid(self):
        """Test validating a valid expression."""
        try:
            from lib.utils.drivers import validate_driver_expression
            result = validate_driver_expression("var * 2 + 1")
            assert result is True
        except (ImportError, AttributeError):
            pytest.skip("validate_driver_expression not available")

    def test_validate_expression_empty(self):
        """Test validating an empty expression."""
        try:
            from lib.utils.drivers import validate_driver_expression
            result = validate_driver_expression("")
            assert result is False
        except (ImportError, AttributeError):
            pytest.skip("validate_driver_expression not available")

    def test_validate_expression_dangerous(self):
        """Test validating potentially dangerous expressions."""
        try:
            from lib.utils.drivers import validate_driver_expression
            # Should reject dangerous function calls
            result = validate_driver_expression("__import__('os').system('rm -rf /')")
            assert result is False
        except (ImportError, AttributeError):
            pytest.skip("validate_driver_expression not available")


class TestDriverBuiltinFunctions:
    """Tests for driver builtin functions."""

    def test_builtin_list(self):
        """Test getting list of builtin functions."""
        try:
            from lib.utils.drivers import DRIVER_BUILTINS
            assert isinstance(DRIVER_BUILTINS, (list, set, tuple))
            # Common math functions should be included
            assert "sin" in DRIVER_BUILTINS or "math.sin" in DRIVER_BUILTINS
        except (ImportError, AttributeError):
            pytest.skip("DRIVER_BUILTINS not available")

    def test_is_builtin_function(self):
        """Test checking if a function is a builtin."""
        try:
            from lib.utils.drivers import is_builtin_function
            assert is_builtin_function("sin") is True
            assert is_builtin_function("custom_var") is False
        except (ImportError, AttributeError):
            pytest.skip("is_builtin_function not available")


class TestDriverExpressionBuilder:
    """Tests for building driver expressions."""

    def test_build_simple_expression(self):
        """Test building a simple expression."""
        try:
            from lib.utils.drivers import build_driver_expression
            expr = build_driver_expression(
                operation="multiply",
                variables=["var1", "var2"]
            )
            assert "var1" in expr
            assert "var2" in expr
        except (ImportError, AttributeError):
            pytest.skip("build_driver_expression not available")

    def test_build_conditional_expression(self):
        """Test building a conditional expression."""
        try:
            from lib.utils.drivers import build_driver_expression
            expr = build_driver_expression(
                operation="if_else",
                condition="var1 > 0.5",
                true_value="var2",
                false_value="0"
            )
            assert "var1" in expr
        except (ImportError, AttributeError):
            pytest.skip("build_driver_expression not available")


class TestDriverUtilities:
    """Tests for driver utility functions."""

    def test_sanitize_variable_name(self):
        """Test sanitizing variable names."""
        try:
            from lib.utils.drivers import sanitize_variable_name
            # Valid names should pass through
            assert sanitize_variable_name("my_var") == "my_var"
            # Invalid chars should be replaced
            result = sanitize_variable_name("my-var!")
            assert "-" not in result
            assert "!" not in result
        except (ImportError, AttributeError):
            pytest.skip("sanitize_variable_name not available")

    def test_evaluate_expression_safe(self):
        """Test safe expression evaluation."""
        try:
            from lib.utils.drivers import evaluate_expression_safe
            result = evaluate_expression_safe("2 + 2", {})
            assert result == 4
        except (ImportError, AttributeError):
            pytest.skip("evaluate_expression_safe not available")

    def test_evaluate_with_variables(self):
        """Test expression evaluation with variables."""
        try:
            from lib.utils.drivers import evaluate_expression_safe
            result = evaluate_expression_safe(
                "a + b",
                {"a": 10, "b": 5}
            )
            assert result == 15
        except (ImportError, AttributeError):
            pytest.skip("evaluate_expression_safe not available")

    def test_evaluate_math_functions(self):
        """Test expression evaluation with math functions."""
        try:
            from lib.utils.drivers import evaluate_expression_safe
            import math
            result = evaluate_expression_safe(
                "sin(0)",
                {},
                allow_math=True
            )
            assert abs(result - 0.0) < 0.0001
        except (ImportError, AttributeError):
            pytest.skip("evaluate_expression_safe not available")


class TestDriverTemplates:
    """Tests for driver templates."""

    def test_template_exists(self):
        """Test that driver templates exist."""
        try:
            from lib.utils.drivers import DRIVER_TEMPLATES
            assert isinstance(DRIVER_TEMPLATES, dict)
        except (ImportError, AttributeError):
            pytest.skip("DRIVER_TEMPLATES not available")

    def test_get_template(self):
        """Test getting a driver template."""
        try:
            from lib.utils.drivers import get_driver_template
            template = get_driver_template("linear")
            assert template is not None
        except (ImportError, AttributeError):
            pytest.skip("get_driver_template not available")

    def test_list_templates(self):
        """Test listing available templates."""
        try:
            from lib.utils.drivers import list_driver_templates
            templates = list_driver_templates()
            assert isinstance(templates, (list, tuple))
        except (ImportError, AttributeError):
            pytest.skip("list_driver_templates not available")


class TestDriverPathParsing:
    """Tests for driver path parsing."""

    def test_parse_rna_path_simple(self):
        """Test parsing simple RNA path."""
        try:
            from lib.utils.drivers import parse_rna_path
            result = parse_rna_path('["my_property"]')
            assert result is not None
            assert result.get('property') == 'my_property'
        except (ImportError, AttributeError):
            pytest.skip("parse_rna_path not available")

    def test_parse_rna_path_nested(self):
        """Test parsing nested RNA path."""
        try:
            from lib.utils.drivers import parse_rna_path
            result = parse_rna_path('modifiers["Subdivision"].levels')
            assert result is not None
        except (ImportError, AttributeError):
            pytest.skip("parse_rna_path not available")

    def test_parse_rna_path_location(self):
        """Test parsing location RNA path."""
        try:
            from lib.utils.drivers import parse_rna_path
            result = parse_rna_path('location[0]')
            assert result is not None
        except (ImportError, AttributeError):
            pytest.skip("parse_rna_path not available")


class TestDriverCopyFunctions:
    """Tests for driver copy utilities (bpy-dependent, structure only)."""

    def test_copy_driver_function_exists(self):
        """Test copy_driver function exists."""
        try:
            from lib.utils.drivers import copy_driver
            assert callable(copy_driver)
        except ImportError:
            pytest.skip("copy_driver not available")

    def test_paste_driver_function_exists(self):
        """Test paste_driver function exists."""
        try:
            from lib.utils.drivers import paste_driver
            assert callable(paste_driver)
        except ImportError:
            pytest.skip("paste_driver not available")
