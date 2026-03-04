"""
Unit tests for lib/geometry_nodes/bundles.py

Tests the Bundle Schema Validator including:
- BundleType enum
- BundleField dataclass
- ValidationError dataclass
- BundleSchema class
- BundleBuilder class
- Pre-defined schemas (PHYSICS_BUNDLE, MATERIAL_BUNDLE, etc.)
- validate_bundle, create_bundle functions

Note: The bundles module itself doesn't require bpy, but it's in the geometry_nodes
package which does. Tests will be skipped when bpy is not available.
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, Any


def _can_import_bundles():
    """Check if bundles module can be imported (requires bpy)."""
    try:
        import bpy
        return True
    except ImportError:
        return False


# Skip all tests in this module if bpy not available
pytestmark = pytest.mark.skipif(
    not _can_import_bundles(),
    reason="bpy not available - bundles tests require Blender environment"
)


@pytest.fixture(scope="module")
def bundles_module():
    """Lazy load the bundles module."""
    try:
        from lib.geometry_nodes import bundles
        return bundles
    except ImportError:
        pytest.skip("bpy not available - bundles module requires Blender environment")


class TestBundleType:
    """Tests for BundleType enum."""

    def test_bundle_type_values(self, bundles_module):
        """Test that BundleType enum has expected values."""
        BundleType = bundles_module.BundleType
        assert BundleType.FLOAT.value == "float"
        assert BundleType.INT.value == "int"
        assert BundleType.VECTOR.value == "vector"
        assert BundleType.COLOR.value == "color"
        assert BundleType.BOOLEAN.value == "bool"
        assert BundleType.STRING.value == "string"
        assert BundleType.GEOMETRY.value == "geometry"
        assert BundleType.COLLECTION.value == "collection"
        assert BundleType.BUNDLE.value == "bundle"

    def test_bundle_type_count(self, bundles_module):
        """Test that all expected types exist."""
        assert len(bundles_module.BundleType) >= 12


class TestBundleField:
    """Tests for BundleField dataclass."""

    def test_default_values(self, bundles_module):
        """Test BundleField default values."""
        BundleField = bundles_module.BundleField
        field = BundleField(name="test", field_type="float")
        assert field.name == "test"
        assert field.field_type == "float"
        assert field.required is True
        assert field.default is None
        assert field.min_value is None
        assert field.max_value is None
        assert field.description == ""
        assert field.nested_schema is None

    def test_custom_values(self, bundles_module):
        """Test BundleField with custom values."""
        BundleField = bundles_module.BundleField
        field = BundleField(
            name="gravity",
            field_type="vector",
            required=False,
            default=(0, 0, -9.8),
            min_value=-100.0,
            max_value=100.0,
            description="Gravity vector"
        )
        assert field.required is False
        assert field.default == (0, 0, -9.8)
        assert field.description == "Gravity vector"

    def test_to_dict(self, bundles_module):
        """Test BundleField.to_dict() serialization."""
        BundleField = bundles_module.BundleField
        field = BundleField(
            name="test",
            field_type="float",
            min_value=0.0,
            max_value=1.0,
            description="Test field"
        )
        data = field.to_dict()
        assert data["name"] == "test"
        assert data["min_value"] == 0.0
        assert data["max_value"] == 1.0


class TestValidationError:
    """Tests for ValidationError dataclass."""

    def test_validation_error_str(self, bundles_module):
        """Test ValidationError string representation."""
        ValidationError = bundles_module.ValidationError
        error = ValidationError(
            field="gravity",
            error_type="missing_required",
            message="Required field 'gravity' is missing"
        )
        assert str(error) == "[missing_required] gravity: Required field 'gravity' is missing"

    def test_validation_error_with_expected(self, bundles_module):
        """Test ValidationError with expected/received."""
        ValidationError = bundles_module.ValidationError
        error = ValidationError(
            field="mass",
            error_type="type_mismatch",
            message="Expected float, got str",
            expected="float",
            received="str"
        )
        assert error.expected == "float"
        assert error.received == "str"


class TestBundleSchema:
    """Tests for BundleSchema class."""

    def test_initialization(self, bundles_module):
        """Test BundleSchema initialization."""
        BundleSchema = bundles_module.BundleSchema
        schema = BundleSchema(
            name="test",
            required_keys={"pos": "vector", "vel": "vector"}
        )
        assert schema.name == "test"
        assert len(schema._fields) == 2

    def test_required_keys(self, bundles_module):
        """Test required keys are properly set."""
        BundleSchema = bundles_module.BundleSchema
        schema = BundleSchema(
            name="test",
            required_keys={"gravity": "vector", "damping": "float"}
        )
        assert "gravity" in schema.required_fields
        assert "damping" in schema.required_fields
        assert len(schema.required_fields) == 2

    def test_optional_keys(self, bundles_module):
        """Test optional keys are properly set."""
        BundleSchema = bundles_module.BundleSchema
        schema = BundleSchema(
            name="test",
            optional_keys={"wind": ("vector", (0, 0, 0)), "mass": "float"}
        )
        assert "wind" in schema.optional_fields
        assert "mass" in schema.optional_fields

    def test_add_field(self, bundles_module):
        """Test add_field method."""
        BundleSchema = bundles_module.BundleSchema
        schema = BundleSchema(name="test")
        schema.add_field("gravity", "vector", required=True)
        assert "gravity" in schema._fields
        assert schema._fields["gravity"].required is True

    def test_add_field_chaining(self, bundles_module):
        """Test add_field returns self for chaining."""
        BundleSchema = bundles_module.BundleSchema
        schema = BundleSchema(name="test")
        result = schema.add_field("a", "float").add_field("b", "int")
        assert result is schema
        assert len(schema._fields) == 2

    def test_add_nested(self, bundles_module):
        """Test add_nested method for nested bundles."""
        BundleSchema = bundles_module.BundleSchema
        nested = BundleSchema(name="nested", required_keys={"x": "float"})
        schema = BundleSchema(name="parent")
        schema.add_nested("child", nested)

        assert "child" in schema._fields
        assert schema._fields["child"].field_type == "bundle"
        assert schema._fields["child"].nested_schema is nested

    def test_validate_valid_data(self, bundles_module):
        """Test validation with valid data."""
        BundleSchema = bundles_module.BundleSchema
        schema = BundleSchema(
            name="test",
            required_keys={"gravity": "vector", "damping": "float"}
        )
        data = {"gravity": (0, 0, -9.8), "damping": 0.98}
        is_valid, errors = schema.validate(data)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_missing_required(self, bundles_module):
        """Test validation catches missing required fields."""
        BundleSchema = bundles_module.BundleSchema
        schema = BundleSchema(
            name="test",
            required_keys={"gravity": "vector", "damping": "float"}
        )
        data = {"gravity": (0, 0, -9.8)}  # Missing damping
        is_valid, errors = schema.validate(data)
        assert is_valid is False
        assert any(e.error_type == "missing_required" for e in errors)

    def test_validate_type_mismatch(self, bundles_module):
        """Test validation catches type mismatches."""
        BundleSchema = bundles_module.BundleSchema
        schema = BundleSchema(
            name="test",
            required_keys={"damping": "float"}
        )
        data = {"damping": "not a float"}
        is_valid, errors = schema.validate(data)
        assert is_valid is False
        assert any(e.error_type == "type_mismatch" for e in errors)

    def test_validate_range_violation(self, bundles_module):
        """Test validation catches range violations."""
        BundleSchema = bundles_module.BundleSchema
        schema = BundleSchema(name="test")
        schema.add_field("mass", "float", min_value=0.0, max_value=100.0)

        is_valid, errors = schema.validate({"mass": 150.0})
        assert is_valid is False
        assert any(e.error_type == "range_violation" for e in errors)

    def test_validate_unknown_field_strict(self, bundles_module):
        """Test validation rejects unknown fields in strict mode."""
        BundleSchema = bundles_module.BundleSchema
        schema = BundleSchema(
            name="test",
            required_keys={"x": "float"}
        )
        data = {"x": 1.0, "unknown": 2.0}
        is_valid, errors = schema.validate(data, strict=True)
        assert is_valid is False
        assert any(e.error_type == "unknown_field" for e in errors)

    def test_validate_unknown_field_non_strict(self, bundles_module):
        """Test validation accepts unknown fields in non-strict mode."""
        BundleSchema = bundles_module.BundleSchema
        schema = BundleSchema(
            name="test",
            required_keys={"x": "float"}
        )
        data = {"x": 1.0, "unknown": 2.0}
        is_valid, errors = schema.validate(data, strict=False)
        assert is_valid is True

    def test_create_default(self, bundles_module):
        """Test create_default generates defaults."""
        BundleSchema = bundles_module.BundleSchema
        schema = BundleSchema(
            name="test",
            required_keys={"gravity": "vector"},
            optional_keys={"mass": ("float", 1.0)}
        )
        defaults = schema.create_default()
        assert "gravity" in defaults
        assert defaults["gravity"] == (0.0, 0.0, 0.0)
        assert defaults["mass"] == 1.0

    def test_to_dict(self, bundles_module):
        """Test to_dict serialization."""
        BundleSchema = bundles_module.BundleSchema
        schema = BundleSchema(
            name="test",
            description="Test schema",
            version="2.0",
            required_keys={"x": "float"}
        )
        data = schema.to_dict()
        assert data["name"] == "test"
        assert data["description"] == "Test schema"
        assert data["version"] == "2.0"
        assert "fields" in data

    def test_registry(self, bundles_module):
        """Test schema registry."""
        BundleSchema = bundles_module.BundleSchema
        schema = BundleSchema(name="unique_test_schema_xyz")
        assert "unique_test_schema_xyz" in BundleSchema.REGISTRY
        assert BundleSchema.get("unique_test_schema_xyz") is schema

    def test_list_schemas(self, bundles_module):
        """Test list_schemas class method."""
        BundleSchema = bundles_module.BundleSchema
        schemas = BundleSchema.list_schemas()
        assert isinstance(schemas, list)
        assert "physics" in schemas  # Pre-defined schema


class TestBundleSchemaTypeValidation:
    """Tests for type validation in BundleSchema."""

    def test_validate_float(self, bundles_module):
        """Test float validation."""
        BundleSchema = bundles_module.BundleSchema
        schema = BundleSchema(name="test", required_keys={"x": "float"})
        assert schema.validate({"x": 1.0})[0] is True
        assert schema.validate({"x": 1})[0] is True  # int is valid for float
        assert schema.validate({"x": "1.0"})[0] is False

    def test_validate_int(self, bundles_module):
        """Test int validation."""
        BundleSchema = bundles_module.BundleSchema
        schema = BundleSchema(name="test", required_keys={"x": "int"})
        assert schema.validate({"x": 1})[0] is True
        assert schema.validate({"x": 1.0})[0] is False  # float not valid for int
        assert schema.validate({"x": True})[0] is False  # bool not valid for int

    def test_validate_vector(self, bundles_module):
        """Test vector validation."""
        BundleSchema = bundles_module.BundleSchema
        schema = BundleSchema(name="test", required_keys={"x": "vector"})
        assert schema.validate({"x": (1, 2, 3)})[0] is True
        assert schema.validate({"x": [1, 2, 3]})[0] is True
        assert schema.validate({"x": (1, 2)})[0] is False  # Wrong length
        assert schema.validate({"x": (1, 2, "3")})[0] is False  # Wrong type

    def test_validate_color(self, bundles_module):
        """Test color validation."""
        BundleSchema = bundles_module.BundleSchema
        schema = BundleSchema(name="test", required_keys={"x": "color"})
        assert schema.validate({"x": (1, 0, 0)})[0] is True  # RGB
        assert schema.validate({"x": (1, 0, 0, 1)})[0] is True  # RGBA
        assert schema.validate({"x": (1, 2)})[0] is False  # Wrong length

    def test_validate_bool(self, bundles_module):
        """Test bool validation."""
        BundleSchema = bundles_module.BundleSchema
        schema = BundleSchema(name="test", required_keys={"x": "bool"})
        assert schema.validate({"x": True})[0] is True
        assert schema.validate({"x": False})[0] is True
        assert schema.validate({"x": 1})[0] is False  # int not valid for bool

    def test_validate_string(self, bundles_module):
        """Test string validation."""
        BundleSchema = bundles_module.BundleSchema
        schema = BundleSchema(name="test", required_keys={"x": "string"})
        assert schema.validate({"x": "hello"})[0] is True
        assert schema.validate({"x": 123})[0] is False

    def test_validate_matrix(self, bundles_module):
        """Test matrix validation."""
        BundleSchema = bundles_module.BundleSchema
        schema = BundleSchema(name="test", required_keys={"x": "matrix"})
        # 4x4 matrix
        matrix = [[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]]
        assert schema.validate({"x": matrix})[0] is True
        assert schema.validate({"x": [[1,2], [3,4]]})[0] is False  # Wrong size

    def test_validate_bundle(self, bundles_module):
        """Test nested bundle validation."""
        BundleSchema = bundles_module.BundleSchema
        nested = BundleSchema(name="nested", required_keys={"y": "float"})
        schema = BundleSchema(name="test")
        schema.add_nested("child", nested)

        is_valid, _ = schema.validate({"child": {"y": 1.0}})
        assert is_valid is True

        is_valid, errors = schema.validate({"child": {"y": "wrong"}})
        assert is_valid is False


class TestBundleBuilder:
    """Tests for BundleBuilder class."""

    def test_initialization(self, bundles_module):
        """Test BundleBuilder initialization."""
        BundleBuilder = bundles_module.BundleBuilder
        builder = BundleBuilder("physics")
        assert builder.schema is not None
        assert builder._data is not None

    def test_initialization_unknown_schema(self, bundles_module):
        """Test BundleBuilder with unknown schema raises."""
        BundleBuilder = bundles_module.BundleBuilder
        with pytest.raises(ValueError):
            BundleBuilder("nonexistent_schema_xyz")

    def test_set(self, bundles_module):
        """Test set method."""
        BundleBuilder = bundles_module.BundleBuilder
        builder = BundleBuilder("physics")
        result = builder.set("gravity", (0, 0, -9.8))
        assert result is builder  # Returns self
        assert builder._data["gravity"] == (0, 0, -9.8)

    def test_set_with_validation(self, bundles_module):
        """Test set method with validation."""
        BundleBuilder = bundles_module.BundleBuilder
        builder = BundleBuilder("physics")
        # Valid field
        builder.set("gravity", (0, 0, -9.8), validate=True)
        # Invalid field
        with pytest.raises(ValueError):
            builder.set("nonexistent_field", 123, validate=True)

    def test_set_if_true(self, bundles_module):
        """Test set_if when condition is true."""
        BundleBuilder = bundles_module.BundleBuilder
        builder = BundleBuilder("physics")
        builder.set_if(True, "damping", 0.98)
        assert builder._data["damping"] == 0.98

    def test_set_if_false(self, bundles_module):
        """Test set_if when condition is false."""
        BundleBuilder = bundles_module.BundleBuilder
        builder = BundleBuilder("physics")
        builder._data.pop("damping", None)  # Remove default
        builder.set_if(False, "damping", 0.98)
        assert "damping" not in builder._data or builder._data.get("damping") != 0.98

    def test_build_valid(self, bundles_module):
        """Test build with valid data."""
        BundleBuilder = bundles_module.BundleBuilder
        bundle = (BundleBuilder("physics")
            .set("gravity", (0, 0, -9.8))
            .set("damping", 0.98)
            .build())
        assert bundle["gravity"] == (0, 0, -9.8)
        assert bundle["damping"] == 0.98

    def test_build_invalid(self, bundles_module):
        """Test build with invalid data raises."""
        BundleBuilder = bundles_module.BundleBuilder
        builder = BundleBuilder("physics")
        builder._data = {}  # Clear required fields
        with pytest.raises(ValueError):
            builder.build(validate=True)

    def test_build_without_validation(self, bundles_module):
        """Test build without validation."""
        BundleBuilder = bundles_module.BundleBuilder
        builder = BundleBuilder("physics")
        builder._data = {}  # Missing required fields
        bundle = builder.build(validate=False)
        assert bundle == {}

    def test_validate(self, bundles_module):
        """Test validate method."""
        BundleBuilder = bundles_module.BundleBuilder
        builder = BundleBuilder("physics")
        builder.set("gravity", (0, 0, -9.8))
        builder.set("damping", 0.98)
        is_valid, errors = builder.validate()
        assert is_valid is True


class TestPreDefinedSchemas:
    """Tests for pre-defined schemas."""

    def test_physics_bundle(self, bundles_module):
        """Test PHYSICS_BUNDLE schema."""
        PHYSICS_BUNDLE = bundles_module.PHYSICS_BUNDLE
        assert PHYSICS_BUNDLE.name == "physics"
        assert "gravity" in PHYSICS_BUNDLE.required_fields
        assert "damping" in PHYSICS_BUNDLE.required_fields

    def test_material_bundle(self, bundles_module):
        """Test MATERIAL_BUNDLE schema."""
        MATERIAL_BUNDLE = bundles_module.MATERIAL_BUNDLE
        assert MATERIAL_BUNDLE.name == "material"
        assert "base_color" in MATERIAL_BUNDLE.required_fields
        assert "roughness" in MATERIAL_BUNDLE.required_fields

    def test_transform_bundle(self, bundles_module):
        """Test TRANSFORM_BUNDLE schema."""
        TRANSFORM_BUNDLE = bundles_module.TRANSFORM_BUNDLE
        assert TRANSFORM_BUNDLE.name == "transform"
        assert "location" in TRANSFORM_BUNDLE.required_fields
        assert "rotation" in TRANSFORM_BUNDLE.required_fields
        assert "scale" in TRANSFORM_BUNDLE.required_fields

    def test_particle_bundle(self, bundles_module):
        """Test PARTICLE_BUNDLE schema."""
        PARTICLE_BUNDLE = bundles_module.PARTICLE_BUNDLE
        assert PARTICLE_BUNDLE.name == "particle"
        assert "position" in PARTICLE_BUNDLE.required_fields
        assert "velocity" in PARTICLE_BUNDLE.required_fields

    def test_camera_bundle(self, bundles_module):
        """Test CAMERA_BUNDLE schema."""
        CAMERA_BUNDLE = bundles_module.CAMERA_BUNDLE
        assert CAMERA_BUNDLE.name == "camera"
        assert "location" in CAMERA_BUNDLE.required_fields

    def test_light_bundle(self, bundles_module):
        """Test LIGHT_BUNDLE schema."""
        LIGHT_BUNDLE = bundles_module.LIGHT_BUNDLE
        assert LIGHT_BUNDLE.name == "light"
        assert "location" in LIGHT_BUNDLE.required_fields
        assert "color" in LIGHT_BUNDLE.required_fields

    def test_volume_bundle(self, bundles_module):
        """Test VOLUME_BUNDLE schema."""
        VOLUME_BUNDLE = bundles_module.VOLUME_BUNDLE
        assert VOLUME_BUNDLE.name == "volume"
        assert "grid_name" in VOLUME_BUNDLE.required_fields

    def test_xpbd_bundle(self, bundles_module):
        """Test XPBD_BUNDLE schema."""
        XPBD_BUNDLE = bundles_module.XPBD_BUNDLE
        assert XPBD_BUNDLE.name == "xpbd_hair"
        assert "stiffness" in XPBD_BUNDLE.required_fields

    def test_all_schemas_registered(self, bundles_module):
        """Test all pre-defined schemas are registered."""
        list_schemas = bundles_module.list_schemas
        schemas = list_schemas()
        assert "physics" in schemas
        assert "material" in schemas
        assert "transform" in schemas
        assert "particle" in schemas


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_validate_bundle(self, bundles_module):
        """Test validate_bundle function."""
        validate_bundle = bundles_module.validate_bundle
        is_valid, errors = validate_bundle(
            "physics",
            {"gravity": (0, 0, -9.8), "damping": 0.98}
        )
        assert is_valid is True

    def test_validate_bundle_unknown_schema(self, bundles_module):
        """Test validate_bundle with unknown schema."""
        validate_bundle = bundles_module.validate_bundle
        is_valid, errors = validate_bundle("nonexistent", {})
        assert is_valid is False
        assert any(e.error_type == "unknown_schema" for e in errors)

    def test_create_bundle(self, bundles_module):
        """Test create_bundle function."""
        create_bundle = bundles_module.create_bundle
        bundle = create_bundle(
            "physics",
            gravity=(0, 0, -10),
            damping=0.95
        )
        assert bundle["gravity"] == (0, 0, -10)
        assert bundle["damping"] == 0.95

    def test_create_bundle_unknown_schema(self, bundles_module):
        """Test create_bundle with unknown schema raises."""
        create_bundle = bundles_module.create_bundle
        with pytest.raises(ValueError):
            create_bundle("nonexistent_schema")

    def test_get_schema(self, bundles_module):
        """Test get_schema function."""
        get_schema = bundles_module.get_schema
        schema = get_schema("physics")
        assert schema is not None
        assert schema.name == "physics"

    def test_get_schema_not_found(self, bundles_module):
        """Test get_schema returns None for unknown schema."""
        get_schema = bundles_module.get_schema
        schema = get_schema("nonexistent")
        assert schema is None

    def test_list_schemas(self, bundles_module):
        """Test list_schemas function."""
        list_schemas = bundles_module.list_schemas
        schemas = list_schemas()
        assert isinstance(schemas, list)
        assert len(schemas) > 0

    def test_print_schema(self, bundles_module):
        """Test print_schema function."""
        print_schema = bundles_module.print_schema
        output = print_schema("physics")
        assert "physics" in output
        assert "REQUIRED" in output or "gravity" in output


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_schema(self, bundles_module):
        """Test schema with no fields."""
        BundleSchema = bundles_module.BundleSchema
        schema = BundleSchema(name="empty")
        is_valid, errors = schema.validate({})
        assert is_valid is True

    def test_schema_with_only_optional_fields(self, bundles_module):
        """Test schema with only optional fields."""
        BundleSchema = bundles_module.BundleSchema
        schema = BundleSchema(
            name="optional_only",
            optional_keys={"x": ("float", 1.0)}
        )
        is_valid, _ = schema.validate({})
        assert is_valid is True

    def test_nested_schema_deep(self, bundles_module):
        """Test deeply nested schemas."""
        BundleSchema = bundles_module.BundleSchema
        level3 = BundleSchema(name="level3", required_keys={"a": "float"})
        level2 = BundleSchema(name="level2")
        level2.add_nested("level3", level3)
        level1 = BundleSchema(name="level1")
        level1.add_nested("level2", level2)

        data = {"level2": {"level3": {"a": 1.0}}}
        is_valid, _ = level1.validate(data)
        assert is_valid is True

    def test_field_with_zero_default(self, bundles_module):
        """Test field with zero as default."""
        BundleSchema = bundles_module.BundleSchema
        schema = BundleSchema(
            name="test",
            optional_keys={"x": ("float", 0.0)}
        )
        defaults = schema.create_default()
        assert defaults["x"] == 0.0

    def test_color_rgba_vs_rgb(self, bundles_module):
        """Test color accepts both RGB and RGBA."""
        BundleSchema = bundles_module.BundleSchema
        schema = BundleSchema(name="test", required_keys={"c": "color"})
        assert schema.validate({"c": (1, 0, 0)})[0] is True
        assert schema.validate({"c": (1, 0, 0, 0.5)})[0] is True
