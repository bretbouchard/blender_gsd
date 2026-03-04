"""
Bundle Schema Validator - Validate and manage Blender 5.0 bundles.

This module provides schema definitions and validation for bundles,
ensuring type safety and correct structure when passing data through
Geometry Nodes.

Usage:
    from lib.geometry_nodes.bundles import BundleSchema, validate_bundle

    # Define a schema
    physics_schema = BundleSchema("physics", required_keys={
        "gravity": "vector",
        "damping": "float",
        "collisions": "collection"
    })

    # Validate bundle data
    data = {"gravity": (0, 0, -9.8), "damping": 0.98}
    is_valid, errors = physics_schema.validate(data)

    # Use pre-defined schemas
    from lib.geometry_nodes.bundles import PHYSICS_BUNDLE, MATERIAL_BUNDLE
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum


class BundleType(Enum):
    """Types of values that can be stored in bundles."""
    FLOAT = "float"
    INT = "int"
    VECTOR = "vector"
    COLOR = "color"
    BOOLEAN = "bool"
    STRING = "string"
    GEOMETRY = "geometry"
    OBJECT = "object"
    COLLECTION = "collection"
    MATERIAL = "material"
    TEXTURE = "texture"
    MATRIX = "matrix"
    BUNDLE = "bundle"  # Nested bundles


@dataclass
class BundleField:
    """Definition of a single field in a bundle schema."""
    name: str
    field_type: str
    required: bool = True
    default: Any = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    description: str = ""
    nested_schema: Optional["BundleSchema"] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "name": self.name,
            "field_type": self.field_type,
            "required": self.required,
            "default": self.default,
            "description": self.description
        }
        if self.min_value is not None:
            result["min_value"] = self.min_value
        if self.max_value is not None:
            result["max_value"] = self.max_value
        if self.nested_schema:
            result["nested_schema"] = self.nested_schema.to_dict()
        return result


@dataclass
class ValidationError:
    """A validation error for a bundle field."""
    field: str
    error_type: str
    message: str
    expected: Optional[str] = None
    received: Optional[str] = None

    def __str__(self) -> str:
        return f"[{self.error_type}] {self.field}: {self.message}"


class BundleSchema:
    """
    Schema definition for Blender 5.0 bundles.

    Bundles are structured data packages that can be passed through
    Geometry Nodes. This class provides validation and documentation.

    Example:
        schema = BundleSchema("material",
            required_keys={"base_color": "color", "roughness": "float"},
            optional_keys={"metallic": ("float", 0.0)}
        )

        is_valid, errors = schema.validate({"base_color": (1,0,0), "roughness": 0.5})
    """

    # Registry of known schemas
    REGISTRY: Dict[str, "BundleSchema"] = {}

    def __init__(
        self,
        name: str,
        required_keys: Optional[Dict[str, str]] = None,
        optional_keys: Optional[Dict[str, Union[str, Tuple[str, Any]]]] = None,
        description: str = "",
        version: str = "1.0"
    ):
        """
        Create a bundle schema.

        Args:
            name: Schema name
            required_keys: Dict of {key_name: type} for required fields
            optional_keys: Dict of {key_name: type} or {key_name: (type, default)}
            description: Human-readable description
            version: Schema version
        """
        self.name = name
        self.description = description
        self.version = version
        self._fields: Dict[str, BundleField] = {}

        # Process required keys
        if required_keys:
            for key_name, key_type in required_keys.items():
                self._fields[key_name] = BundleField(
                    name=key_name,
                    field_type=key_type,
                    required=True
                )

        # Process optional keys
        if optional_keys:
            for key_name, key_def in optional_keys.items():
                if isinstance(key_def, tuple):
                    key_type, default = key_def
                else:
                    key_type = key_def
                    default = None

                self._fields[key_name] = BundleField(
                    name=key_name,
                    field_type=key_type,
                    required=False,
                    default=default
                )

        # Register in global registry
        self.REGISTRY[name] = self

    def add_field(
        self,
        name: str,
        field_type: str,
        required: bool = True,
        default: Any = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        description: str = ""
    ) -> "BundleSchema":
        """
        Add a field to the schema.

        Args:
            name: Field name
            field_type: Type of the field (float, int, vector, color, etc.)
            required: Whether the field is required
            default: Default value for optional fields
            min_value: Minimum value (for numeric types)
            max_value: Maximum value (for numeric types)
            description: Field description

        Returns:
            Self for chaining
        """
        self._fields[name] = BundleField(
            name=name,
            field_type=field_type,
            required=required,
            default=default,
            min_value=min_value,
            max_value=max_value,
            description=description
        )
        return self

    def add_nested(
        self,
        name: str,
        schema: "BundleSchema",
        required: bool = True
    ) -> "BundleSchema":
        """
        Add a nested bundle field.

        Args:
            name: Field name
            schema: Schema for the nested bundle
            required: Whether the field is required

        Returns:
            Self for chaining
        """
        self._fields[name] = BundleField(
            name=name,
            field_type="bundle",
            required=required,
            nested_schema=schema
        )
        return self

    @property
    def required_fields(self) -> List[str]:
        """Get list of required field names."""
        return [f.name for f in self._fields.values() if f.required]

    @property
    def optional_fields(self) -> List[str]:
        """Get list of optional field names."""
        return [f.name for f in self._fields.values() if not f.required]

    def validate(
        self,
        data: Dict[str, Any],
        strict: bool = False
    ) -> Tuple[bool, List[ValidationError]]:
        """
        Validate bundle data against this schema.

        Args:
            data: Bundle data to validate
            strict: If True, reject unknown fields

        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors: List[ValidationError] = []

        # Check for missing required fields
        for field_name, field_def in self._fields.items():
            if field_def.required and field_name not in data:
                errors.append(ValidationError(
                    field=field_name,
                    error_type="missing_required",
                    message=f"Required field '{field_name}' is missing"
                ))

        # Validate present fields
        for key, value in data.items():
            if key not in self._fields:
                if strict:
                    errors.append(ValidationError(
                        field=key,
                        error_type="unknown_field",
                        message=f"Unknown field '{key}' not in schema"
                    ))
                continue

            field_def = self._fields[key]
            field_errors = self._validate_field(field_def, value)
            errors.extend(field_errors)

        return len(errors) == 0, errors

    def _validate_field(
        self,
        field: BundleField,
        value: Any
    ) -> List[ValidationError]:
        """Validate a single field value."""
        errors: List[ValidationError] = []

        # Type validation
        type_valid, type_error = self._validate_type(field.field_type, value)
        if not type_valid:
            errors.append(ValidationError(
                field=field.name,
                error_type="type_mismatch",
                message=type_error,
                expected=field.field_type,
                received=type(value).__name__
            ))
            return errors  # Skip further validation if type is wrong

        # Range validation for numeric types
        if field.field_type in ("float", "int"):
            if field.min_value is not None and value < field.min_value:
                errors.append(ValidationError(
                    field=field.name,
                    error_type="range_violation",
                    message=f"Value {value} is below minimum {field.min_value}"
                ))
            if field.max_value is not None and value > field.max_value:
                errors.append(ValidationError(
                    field=field.name,
                    error_type="range_violation",
                    message=f"Value {value} is above maximum {field.max_value}"
                ))

        # Nested bundle validation
        if field.field_type == "bundle" and field.nested_schema:
            if isinstance(value, dict):
                nested_valid, nested_errors = field.nested_schema.validate(value)
                for err in nested_errors:
                    errors.append(ValidationError(
                        field=f"{field.name}.{err.field}",
                        error_type=err.error_type,
                        message=err.message
                    ))

        return errors

    def _validate_type(self, expected_type: str, value: Any) -> Tuple[bool, str]:
        """Validate that a value matches the expected type."""
        type_validators = {
            "float": lambda v: isinstance(v, (int, float)),
            "int": lambda v: isinstance(v, int) and not isinstance(v, bool),
            "vector": lambda v: (isinstance(v, (tuple, list)) and len(v) == 3 and
                                all(isinstance(x, (int, float)) for x in v)),
            "color": lambda v: (isinstance(v, (tuple, list)) and len(v) in (3, 4) and
                               all(isinstance(x, (int, float)) for x in v)),
            "bool": lambda v: isinstance(v, bool),
            "string": lambda v: isinstance(v, str),
            "geometry": lambda v: hasattr(v, 'name'),  # Blender object check
            "object": lambda v: hasattr(v, 'name'),
            "collection": lambda v: hasattr(v, 'name'),
            "material": lambda v: hasattr(v, 'name'),
            "texture": lambda v: hasattr(v, 'name'),
            "matrix": lambda v: (isinstance(v, (tuple, list)) and len(v) == 4 and
                                all(len(row) == 4 for row in v)),
            "bundle": lambda v: isinstance(v, dict),
        }

        validator = type_validators.get(expected_type)
        if not validator:
            return True, f"Unknown type '{expected_type}'"

        if validator(value):
            return True, ""

        return False, f"Expected {expected_type}, got {type(value).__name__}"

    def create_default(self) -> Dict[str, Any]:
        """
        Create a bundle with default values.

        Returns:
            Dict with all fields set to their defaults
        """
        result = {}

        for field_name, field_def in self._fields.items():
            if field_def.default is not None:
                result[field_name] = field_def.default
            elif field_def.field_type == "float":
                result[field_name] = 0.0
            elif field_def.field_type == "int":
                result[field_name] = 0
            elif field_def.field_type == "vector":
                result[field_name] = (0.0, 0.0, 0.0)
            elif field_def.field_type == "color":
                result[field_name] = (1.0, 1.0, 1.0, 1.0)
            elif field_def.field_type == "bool":
                result[field_name] = False
            elif field_def.field_type == "string":
                result[field_name] = ""
            elif field_def.field_type == "bundle" and field_def.nested_schema:
                result[field_name] = field_def.nested_schema.create_default()

        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "fields": {name: field.to_dict() for name, field in self._fields.items()}
        }

    @classmethod
    def get(cls, name: str) -> Optional["BundleSchema"]:
        """Get a registered schema by name."""
        return cls.REGISTRY.get(name)

    @classmethod
    def list_schemas(cls) -> List[str]:
        """List all registered schema names."""
        return list(cls.REGISTRY.keys())

    def __repr__(self) -> str:
        return f"BundleSchema('{self.name}', fields={len(self._fields)})"


# ============================================================================
# PRE-DEFINED SCHEMAS
# ============================================================================

# Physics Bundle Schema
PHYSICS_BUNDLE = BundleSchema(
    name="physics",
    description="Physics simulation parameters for Blender 5.0",
    required_keys={
        "gravity": "vector",
        "damping": "float",
    },
    optional_keys={
        "wind": ("vector", (0.0, 0.0, 0.0)),
        "time_step": ("float", 0.016),
        "substeps": ("int", 1),
    }
)
PHYSICS_BUNDLE.add_field("collisions", "collection", required=False)
PHYSICS_BUNDLE.add_field("mass", "float", required=False, min_value=0.0)
PHYSICS_BUNDLE.add_field("drag", "float", required=False, min_value=0.0, max_value=1.0)

# Material Bundle Schema
MATERIAL_BUNDLE = BundleSchema(
    name="material",
    description="Material properties bundle for Geometry Nodes",
    required_keys={
        "base_color": "color",
        "roughness": "float",
    },
    optional_keys={
        "metallic": ("float", 0.0),
        "ior": ("float", 1.45),
        "transmission": ("float", 0.0),
        "emission": ("color", (0.0, 0.0, 0.0, 1.0)),
    }
)
MATERIAL_BUNDLE.add_field("normal_strength", "float", required=False, min_value=0.0, max_value=2.0)
MATERIAL_BUNDLE.add_field("subsurface", "float", required=False, min_value=0.0, max_value=1.0)

# Transform Bundle Schema
TRANSFORM_BUNDLE = BundleSchema(
    name="transform",
    description="Transform data for instances",
    required_keys={
        "location": "vector",
        "rotation": "vector",
        "scale": "vector",
    }
)

# Particle Bundle Schema
PARTICLE_BUNDLE = BundleSchema(
    name="particle",
    description="Particle state for simulation",
    required_keys={
        "position": "vector",
        "velocity": "vector",
    },
    optional_keys={
        "mass": ("float", 1.0),
        "age": ("float", 0.0),
        "life": ("float", 100.0),
        "size": ("float", 1.0),
    }
)
PARTICLE_BUNDLE.add_field("id", "int", required=False)

# Camera Bundle Schema
CAMERA_BUNDLE = BundleSchema(
    name="camera",
    description="Camera output from Geometry Nodes (5.0)",
    required_keys={
        "location": "vector",
        "rotation": "vector",
    },
    optional_keys={
        "fov": ("float", 50.0),
        "near_clip": ("float", 0.1),
        "far_clip": ("float", 1000.0),
    }
)
CAMERA_BUNDLE.add_field("target", "vector", required=False)

# Light Bundle Schema
LIGHT_BUNDLE = BundleSchema(
    name="light",
    description="Light output from Geometry Nodes (5.0)",
    required_keys={
        "location": "vector",
        "color": "color",
        "power": "float",
    },
    optional_keys={
        "type": ("string", "POINT"),
        "radius": ("float", 0.1),
    }
)

# Volume Grid Bundle Schema
VOLUME_BUNDLE = BundleSchema(
    name="volume",
    description="Volume grid parameters",
    required_keys={
        "grid_name": "string",
        "voxel_size": "float",
    },
    optional_keys={
        "background": ("float", 0.0),
        "sdf": ("bool", False),
    }
)
VOLUME_BUNDLE.add_field("resolution", "int", required=False)

# XPBD Hair Bundle Schema (for future use)
XPBD_BUNDLE = BundleSchema(
    name="xpbd_hair",
    description="XPBD solver parameters for hair simulation (Blender 5.2+)",
    required_keys={
        "stiffness": "float",
        "damping": "float",
    },
    optional_keys={
        "bend_stiffness": ("float", 0.5),
        "stretch_stiffness": ("float", 1.0),
        "self_collision": ("bool", True),
    }
)
XPBD_BUNDLE.add_field("strand_count", "int", required=False, min_value=1)
XPBD_BUNDLE.add_field("strand_length", "float", required=False, min_value=0.1)


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_bundle(
    schema_name: str,
    data: Dict[str, Any],
    strict: bool = False
) -> Tuple[bool, List[ValidationError]]:
    """
    Validate bundle data against a named schema.

    Args:
        schema_name: Name of the registered schema
        data: Bundle data to validate
        strict: If True, reject unknown fields

    Returns:
        Tuple of (is_valid, list of errors)
    """
    schema = BundleSchema.get(schema_name)
    if not schema:
        return False, [ValidationError(
            field="",
            error_type="unknown_schema",
            message=f"Schema '{schema_name}' not found"
        )]

    return schema.validate(data, strict)


def create_bundle(schema_name: str, **kwargs) -> Dict[str, Any]:
    """
    Create a bundle from a schema with provided values.

    Args:
        schema_name: Name of the registered schema
        **kwargs: Field values

    Returns:
        Bundle dict with defaults filled in
    """
    schema = BundleSchema.get(schema_name)
    if not schema:
        raise ValueError(f"Schema '{schema_name}' not found")

    bundle = schema.create_default()
    bundle.update(kwargs)
    return bundle


def get_schema(schema_name: str) -> Optional[BundleSchema]:
    """Get a registered schema by name."""
    return BundleSchema.get(schema_name)


def list_schemas() -> List[str]:
    """List all registered schema names."""
    return BundleSchema.list_schemas()


def print_schema(schema_name: str) -> str:
    """Print schema documentation."""
    schema = BundleSchema.get(schema_name)
    if not schema:
        return f"Schema '{schema_name}' not found"

    lines = [
        f"╔══════════════════════════════════════╗",
        f"║  Bundle Schema: {schema.name:<20} ║",
        f"╠══════════════════════════════════════╣",
        f"║  {schema.description:<36} ║",
        f"╠══════════════════════════════════════╣",
    ]

    # Required fields
    if schema.required_fields:
        lines.append("║  REQUIRED FIELDS:                    ║")
        for field_name in schema.required_fields:
            field = schema._fields[field_name]
            lines.append(f"║    {field_name:<15} ({field.field_type:<8})     ║")

    # Optional fields
    if schema.optional_fields:
        lines.append("║  OPTIONAL FIELDS:                    ║")
        for field_name in schema.optional_fields:
            field = schema._fields[field_name]
            default_str = f"={field.default}" if field.default is not None else ""
            lines.append(f"║    {field_name:<15} ({field.field_type:<8}){default_str:<6} ║")

    lines.append("╚══════════════════════════════════════╝")

    return "\n".join(lines)


# ============================================================================
# BUNDLE BUILDER CLASS
# ============================================================================

class BundleBuilder:
    """
    Fluent builder for creating bundles.

    Usage:
        bundle = (BundleBuilder("physics")
            .set("gravity", (0, 0, -9.8))
            .set("damping", 0.98)
            .set("wind", (0.5, 0, 0))
            .build())
    """

    def __init__(self, schema_name: str):
        """
        Initialize builder with a schema.

        Args:
            schema_name: Name of the registered schema
        """
        self.schema = BundleSchema.get(schema_name)
        if not self.schema:
            raise ValueError(f"Schema '{schema_name}' not found")

        self._data: Dict[str, Any] = self.schema.create_default()
        self._schema_name = schema_name

    def set(self, field: str, value: Any, validate: bool = False) -> "BundleBuilder":
        """
        Set a field value.

        Args:
            field: Field name
            value: Field value
            validate: If True, immediately validate the field exists in schema

        Returns:
            Self for chaining

        Raises:
            ValueError: If validate=True and field is not in schema
        """
        if validate and field not in self.schema._fields:
            raise ValueError(
                f"Unknown field '{field}' in schema '{self.schema.name}'. "
                f"Available fields: {list(self.schema._fields.keys())}"
            )
        self._data[field] = value
        return self

    def set_if(self, condition: bool, field: str, value: Any) -> "BundleBuilder":
        """
        Set a field value only if condition is true.

        Args:
            condition: Whether to set the value
            field: Field name
            value: Field value

        Returns:
            Self for chaining
        """
        if condition:
            self._data[field] = value
        return self

    def build(self, validate: bool = True) -> Dict[str, Any]:
        """
        Build the bundle.

        Args:
            validate: Whether to validate before returning

        Returns:
            The bundle dict

        Raises:
            ValueError: If validation fails
        """
        if validate:
            is_valid, errors = self.schema.validate(self._data)
            if not is_valid:
                error_msg = "\n".join(str(e) for e in errors)
                raise ValueError(f"Bundle validation failed:\n{error_msg}")

        return self._data.copy()

    def validate(self) -> Tuple[bool, List[ValidationError]]:
        """Validate current bundle state."""
        return self.schema.validate(self._data)
