"""
Safety utilities for Blender GSD pipeline.

Provides atomic writes, schema validation, and data integrity utilities
to prevent data loss and ensure robust file operations.

Usage:
    from lib.utils.safety import atomic_write, validate_yaml, SafeYAML

    # Atomic write
    atomic_write(path, data)

    # Validated load
    config = SafeYAML.load(path, schema='pose')
"""

import os
import tempfile
import shutil
import warnings
from pathlib import Path
from typing import Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

# Try to import yaml, provide fallback error
try:
    import yaml
except ImportError:
    raise ImportError("PyYAML required: pip install pyyaml")

# Try to import jsonschema for validation
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    warnings.warn("jsonschema not installed. Schema validation disabled. pip install jsonschema")


# ============================================================================
# SCHEMAS
# ============================================================================

SCHEMAS = {
    'pose': {
        "type": "object",
        "required": ["id", "name", "bones"],
        "properties": {
            "id": {"type": "string", "pattern": "^[a-z0-9_]+$"},
            "name": {"type": "string", "minLength": 1},
            "category": {"type": "string", "enum": ["rest", "locomotion", "action", "expression", "hand", "custom"]},
            "rig_type": {"type": "string"},
            "description": {"type": "string"},
            "bones": {
                "type": "object",
                "additionalProperties": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
                        "rotation": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
                        "scale": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
                        "rotation_quat": {"type": "array", "items": {"type": "number"}, "minItems": 4, "maxItems": 4},
                    }
                }
            },
            "metadata": {"type": "object"}
        }
    },

    'rig': {
        "type": "object",
        "required": ["id", "name", "bones"],
        "properties": {
            "id": {"type": "string", "pattern": "^[a-z0-9_]+$"},
            "name": {"type": "string"},
            "type": {"type": "string"},
            "bones": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id"],
                    "properties": {
                        "id": {"type": "string"},
                        "parent": {"type": "string"},
                        "head": {"type": "array", "items": {"type": "number"}, "minItems": 3},
                        "tail": {"type": "array", "items": {"type": "number"}, "minItems": 3},
                        "roll": {"type": "number"},
                    }
                }
            }
        }
    },

    'vehicle': {
        "type": "object",
        "required": ["id", "name", "type"],
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "type": {"type": "string", "enum": ["automobile", "truck", "plane", "helicopter", "robot", "tank", "boat", "custom"]},
            "dimensions": {
                "type": "object",
                "properties": {
                    "length": {"type": "number", "minimum": 0},
                    "width": {"type": "number", "minimum": 0},
                    "height": {"type": "number", "minimum": 0},
                    "wheelbase": {"type": "number", "minimum": 0},
                }
            },
            "wheels": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "position"],
                    "properties": {
                        "id": {"type": "string"},
                        "position": {"type": "array", "items": {"type": "number"}, "minItems": 3},
                        "radius": {"type": "number", "minimum": 0},
                        "steering": {"type": "boolean"},
                        "driven": {"type": "boolean"},
                    }
                }
            }
        }
    },

    'crowd': {
        "type": "object",
        "required": ["id", "name"],
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "agent": {
                "type": "object",
                "properties": {
                    "mesh": {"type": "string"},
                    "rig": {"type": "string"},
                    "animations": {"type": "array", "items": {"type": "string"}},
                }
            },
            "spawn": {
                "type": "object",
                "properties": {
                    "count": {"type": "integer", "minimum": 0, "maximum": 10000},
                    "area": {"type": "array", "minItems": 2, "maxItems": 2},
                }
            }
        }
    },

    'layer_stack': {
        "type": "object",
        "required": ["rig_id", "layers"],
        "properties": {
            "rig_id": {"type": "string"},
            "active_layer": {"type": ["string", "null"]},
            "layers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "name"],
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "type": {"type": "string", "enum": ["base", "override", "additive", "mix"]},
                        "opacity": {"type": "number", "minimum": 0, "maximum": 1},
                        "mute": {"type": "boolean"},
                        "solo": {"type": "boolean"},
                        "bone_mask": {"type": "array", "items": {"type": "string"}},
                        "order": {"type": "integer", "minimum": 0},
                    }
                }
            }
        }
    }
}


# ============================================================================
# ATOMIC WRITE
# ============================================================================

def atomic_write(
    path: Union[str, Path],
    data: Dict[str, Any],
    encoding: str = 'utf-8',
    create_backup: bool = True
) -> Path:
    """
    Write data to file atomically.

    Uses write-to-temp-then-rename pattern to prevent corruption
    on crash or interruption. Works on all POSIX systems.

    Args:
        path: Target file path
        data: Dictionary to write as YAML
        encoding: File encoding (default: utf-8)
        create_backup: Create .bak of existing file (default: True)

    Returns:
        Path to written file

    Raises:
        IOError: If write fails (original file unchanged)
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Create backup if file exists
    if create_backup and path.exists():
        backup_path = path.with_suffix(path.suffix + '.bak')
        shutil.copy2(path, backup_path)

    # Write to temp file in same directory (ensures same filesystem)
    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.stem}_",
        suffix=path.suffix
    )

    try:
        # Write data
        with os.fdopen(fd, 'w', encoding=encoding) as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        # Atomic rename (POSIX guarantees atomicity)
        os.replace(tmp_path, path)

        logger.debug(f"Atomic write successful: {path}")
        return path

    except Exception as e:
        # Clean up temp file on failure
        try:
            os.unlink(tmp_path)
        except:
            pass

        logger.error(f"Atomic write failed: {path} - {e}")
        raise IOError(f"Failed to write {path}: {e}")


# ============================================================================
# SCHEMA VALIDATION
# ============================================================================

def validate_yaml(
    data: Dict[str, Any],
    schema_name: str,
    strict: bool = False
) -> bool:
    """
    Validate data against a schema.

    Args:
        data: Dictionary to validate
        schema_name: Name of schema (pose, rig, vehicle, crowd, layer_stack)
        strict: If True, raise exception on validation failure

    Returns:
        True if valid, False otherwise

    Raises:
        jsonschema.ValidationError: If strict=True and validation fails
        KeyError: If schema not found
    """
    if not HAS_JSONSCHEMA:
        if strict:
            raise ImportError("jsonschema required for strict validation")
        warnings.warn("jsonschema not installed, skipping validation")
        return True

    if schema_name not in SCHEMAS:
        raise KeyError(f"Unknown schema: {schema_name}. Available: {list(SCHEMAS.keys())}")

    schema = SCHEMAS[schema_name]

    try:
        jsonschema.validate(data, schema)
        return True
    except jsonschema.ValidationError as e:
        if strict:
            raise
        logger.warning(f"Validation failed for {schema_name}: {e.message}")
        return False


def get_schema(schema_name: str) -> Dict[str, Any]:
    """Get a schema by name."""
    if schema_name not in SCHEMAS:
        raise KeyError(f"Unknown schema: {schema_name}")
    return SCHEMAS[schema_name].copy()


# ============================================================================
# SAFE YAML CLASS
# ============================================================================

class SafeYAML:
    """
    Safe YAML operations with validation and atomic writes.

    Usage:
        # Load with validation
        config = SafeYAML.load('pose.yaml', schema='pose')

        # Save with validation and atomic write
        SafeYAML.save('pose.yaml', config, schema='pose')
    """

    @staticmethod
    def load(
        path: Union[str, Path],
        schema: Optional[str] = None,
        strict: bool = False,
        default: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Load YAML file with optional validation.

        Args:
            path: File path
            schema: Schema name for validation (optional)
            strict: Raise on validation failure
            default: Default value if file doesn't exist

        Returns:
            Loaded data dictionary
        """
        path = Path(path)

        if not path.exists():
            if default is not None:
                return default.copy()
            raise FileNotFoundError(f"File not found: {path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if data is None:
            data = {}

        # Validate if schema provided
        if schema:
            if not validate_yaml(data, schema, strict=strict):
                logger.warning(f"Validation failed for {path}")

        return data

    @staticmethod
    def save(
        path: Union[str, Path],
        data: Dict[str, Any],
        schema: Optional[str] = None,
        strict: bool = False,
        create_backup: bool = True
    ) -> Path:
        """
        Save YAML file with validation and atomic write.

        Args:
            path: File path
            data: Data to save
            schema: Schema name for validation (optional)
            strict: Raise on validation failure
            create_backup: Create backup of existing file

        Returns:
            Path to saved file
        """
        # Validate before saving
        if schema:
            if not validate_yaml(data, schema, strict=strict):
                if strict:
                    raise ValueError(f"Data fails {schema} schema validation")
                logger.warning(f"Saving data that fails {schema} schema validation")

        return atomic_write(path, data, create_backup=create_backup)


# ============================================================================
# ID GENERATION
# ============================================================================

def generate_unique_id(
    base_name: str,
    existing_ids: set,
    separator: str = '_',
    max_attempts: int = 100
) -> str:
    """
    Generate a unique ID from a base name.

    Args:
        base_name: Base name to use
        existing_ids: Set of existing IDs to avoid
        separator: Separator for suffix
        max_attempts: Maximum attempts before raising

    Returns:
        Unique ID string
    """
    # Clean base name
    base_id = base_name.lower().replace(' ', '_').replace('-', '_')
    base_id = ''.join(c for c in base_id if c.isalnum() or c == '_')

    # Try base first
    if base_id not in existing_ids:
        return base_id

    # Try incrementing suffix
    for i in range(1, max_attempts + 1):
        candidate = f"{base_id}{separator}{i}"
        if candidate not in existing_ids:
            return candidate

    raise ValueError(f"Could not generate unique ID from {base_name} after {max_attempts} attempts")


def id_exists(id_to_check: str, existing_ids: set) -> bool:
    """Check if an ID already exists."""
    return id_to_check in existing_ids


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_file_path(path: Union[str, Path], must_exist: bool = True) -> Path:
    """
    Validate a file path.

    Args:
        path: Path to validate
        must_exist: If True, file must exist

    Returns:
        Validated Path object

    Raises:
        FileNotFoundError: If must_exist=True and file doesn't exist
        ValueError: If path is invalid
    """
    path = Path(path)

    if not path.is_absolute():
        raise ValueError(f"Path must be absolute: {path}")

    if must_exist and not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    return path


def validate_range(value: float, name: str, min_val: float, max_val: float) -> float:
    """
    Validate a value is within range.

    Args:
        value: Value to validate
        name: Name for error message
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Clamped value

    Raises:
        ValueError: If value is NaN
    """
    import math

    if math.isnan(value):
        raise ValueError(f"{name} cannot be NaN")

    if value < min_val:
        warnings.warn(f"{name}={value} below minimum {min_val}, clamping")
        return min_val

    if value > max_val:
        warnings.warn(f"{name}={value} above maximum {max_val}, clamping")
        return max_val

    return value
