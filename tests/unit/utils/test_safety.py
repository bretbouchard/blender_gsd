"""
Tests for safety module.

Tests run WITHOUT Blender (bpy) by testing only non-Blender-dependent code paths.
"""

import pytest
import os
import tempfile
import warnings
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestSafetyModule:
    """Tests for safety module structure."""

    def test_module_imports(self):
        """Test that the safety module can be imported."""
        from lib.utils import safety
        assert safety is not None

    def test_module_exports_functions(self):
        """Test module exports expected functions."""
        from lib.utils import safety
        assert hasattr(safety, 'atomic_write')
        assert hasattr(safety, 'validate_yaml')
        assert hasattr(safety, 'get_schema')
        assert hasattr(safety, 'SafeYAML')
        assert hasattr(safety, 'generate_unique_id')


class TestSchemas:
    """Tests for schema definitions."""

    def test_schemas_exist(self):
        """Test that SCHEMAS dict exists and has entries."""
        from lib.utils.safety import SCHEMAS
        assert isinstance(SCHEMAS, dict)
        assert len(SCHEMAS) > 0

    def test_pose_schema_structure(self):
        """Test pose schema has required fields."""
        from lib.utils.safety import SCHEMAS
        pose_schema = SCHEMAS['pose']
        assert 'required' in pose_schema
        assert 'id' in pose_schema['required']
        assert 'name' in pose_schema['required']
        assert 'bones' in pose_schema['required']

    def test_rig_schema_structure(self):
        """Test rig schema has required fields."""
        from lib.utils.safety import SCHEMAS
        rig_schema = SCHEMAS['rig']
        assert 'required' in rig_schema
        assert 'id' in rig_schema['required']
        assert 'bones' in rig_schema['required']

    def test_vehicle_schema_structure(self):
        """Test vehicle schema has required fields."""
        from lib.utils.safety import SCHEMAS
        vehicle_schema = SCHEMAS['vehicle']
        assert 'required' in vehicle_schema
        assert 'id' in vehicle_schema['required']
        assert 'type' in vehicle_schema['required']

    def test_get_schema(self):
        """Test get_schema returns a copy of schema."""
        from lib.utils.safety import get_schema
        schema = get_schema('pose')
        assert isinstance(schema, dict)
        assert 'required' in schema

    def test_get_schema_unknown(self):
        """Test get_schema raises for unknown schema."""
        from lib.utils.safety import get_schema
        with pytest.raises(KeyError):
            get_schema('unknown_schema')


class TestValidateYaml:
    """Tests for validate_yaml function."""

    def test_validate_yaml_valid_pose(self):
        """Test validating a valid pose."""
        from lib.utils.safety import validate_yaml
        data = {
            'id': 'test_pose',
            'name': 'Test Pose',
            'bones': {
                'spine': {
                    'location': [0, 0, 0],
                    'rotation': [0, 0, 0]
                }
            }
        }
        result = validate_yaml(data, 'pose')
        assert result is True

    def test_validate_yaml_invalid_missing_required(self):
        """Test validating data missing required fields."""
        from lib.utils.safety import validate_yaml
        data = {'name': 'Test'}  # Missing 'id' and 'bones'
        result = validate_yaml(data, 'pose')
        assert result is False

    def test_validate_yaml_unknown_schema(self):
        """Test validating with unknown schema."""
        from lib.utils.safety import validate_yaml
        with pytest.raises(KeyError):
            validate_yaml({}, 'unknown_schema')

    def test_validate_yaml_strict_raises(self):
        """Test validate_yaml with strict=True raises on error."""
        from lib.utils.safety import validate_yaml
        data = {'name': 'Test'}  # Invalid
        with pytest.raises(Exception):  # jsonschema.ValidationError
            validate_yaml(data, 'pose', strict=True)


class TestAtomicWrite:
    """Tests for atomic_write function."""

    def test_atomic_write_creates_file(self):
        """Test atomic_write creates a file."""
        from lib.utils.safety import atomic_write
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.yaml"
            data = {'key': 'value'}
            result = atomic_write(path, data)
            assert result.exists()
            assert result == path

    def test_atomic_write_content(self):
        """Test atomic_write writes correct content."""
        from lib.utils.safety import atomic_write
        import yaml
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.yaml"
            data = {'key': 'value', 'nested': {'a': 1}}
            atomic_write(path, data)

            with open(path, 'r') as f:
                loaded = yaml.safe_load(f)
            assert loaded == data

    def test_atomic_write_creates_parent_dirs(self):
        """Test atomic_write creates parent directories."""
        from lib.utils.safety import atomic_write
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "subdir" / "nested" / "test.yaml"
            data = {'key': 'value'}
            result = atomic_write(path, data)
            assert result.exists()

    def test_atomic_write_creates_backup(self):
        """Test atomic_write creates backup of existing file."""
        from lib.utils.safety import atomic_write
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.yaml"
            # Write initial file
            atomic_write(path, {'version': 1})
            # Overwrite with backup
            atomic_write(path, {'version': 2}, create_backup=True)
            # Check backup exists
            backup_path = path.with_suffix('.yaml.bak')
            assert backup_path.exists()

    def test_atomic_write_no_backup(self):
        """Test atomic_write without backup."""
        from lib.utils.safety import atomic_write
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.yaml"
            # Write initial file
            atomic_write(path, {'version': 1})
            # Overwrite without backup
            atomic_write(path, {'version': 2}, create_backup=False)
            # Check no backup exists
            backup_path = path.with_suffix('.yaml.bak')
            assert not backup_path.exists()


class TestSafeYAML:
    """Tests for SafeYAML class."""

    def test_safe_yaml_load(self):
        """Test SafeYAML.load loads a file."""
        from lib.utils.safety import SafeYAML
        import yaml
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.yaml"
            data = {'key': 'value'}
            with open(path, 'w') as f:
                yaml.dump(data, f)

            loaded = SafeYAML.load(path)
            assert loaded == data

    def test_safe_yaml_load_not_found(self):
        """Test SafeYAML.load raises for missing file."""
        from lib.utils.safety import SafeYAML
        with pytest.raises(FileNotFoundError):
            SafeYAML.load('/nonexistent/path.yaml')

    def test_safe_yaml_load_with_default(self):
        """Test SafeYAML.load returns default for missing file."""
        from lib.utils.safety import SafeYAML
        default = {'default': True}
        result = SafeYAML.load('/nonexistent/path.yaml', default=default)
        assert result == default

    def test_safe_yaml_load_with_validation(self):
        """Test SafeYAML.load with schema validation."""
        from lib.utils.safety import SafeYAML
        import yaml
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.yaml"
            data = {
                'id': 'test_pose',
                'name': 'Test',
                'bones': {}
            }
            with open(path, 'w') as f:
                yaml.dump(data, f)

            loaded = SafeYAML.load(path, schema='pose')
            assert loaded['id'] == 'test_pose'

    def test_safe_yaml_save(self):
        """Test SafeYAML.save saves a file."""
        from lib.utils.safety import SafeYAML
        import yaml
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.yaml"
            data = {'key': 'value'}
            SafeYAML.save(path, data)

            with open(path, 'r') as f:
                loaded = yaml.safe_load(f)
            assert loaded == data

    def test_safe_yaml_save_with_validation(self):
        """Test SafeYAML.save validates before saving."""
        from lib.utils.safety import SafeYAML
        import yaml
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.yaml"
            data = {
                'id': 'test_pose',
                'name': 'Test',
                'bones': {}
            }
            SafeYAML.save(path, data, schema='pose')

            with open(path, 'r') as f:
                loaded = yaml.safe_load(f)
            assert loaded['id'] == 'test_pose'


class TestGenerateUniqueId:
    """Tests for generate_unique_id function."""

    def test_generate_unique_id_simple(self):
        """Test generating a simple unique ID."""
        from lib.utils.safety import generate_unique_id
        result = generate_unique_id("Test Name", existing_ids=set())
        assert result == "test_name"

    def test_generate_unique_id_with_existing(self):
        """Test generating unique ID when base already exists."""
        from lib.utils.safety import generate_unique_id
        existing = {"test_name"}
        result = generate_unique_id("Test Name", existing_ids=existing)
        assert result == "test_name_1"

    def test_generate_unique_id_multiple_existing(self):
        """Test generating unique ID with multiple existing."""
        from lib.utils.safety import generate_unique_id
        existing = {"test_name", "test_name_1", "test_name_2"}
        result = generate_unique_id("Test Name", existing_ids=existing)
        assert result == "test_name_3"

    def test_generate_unique_id_sanitizes(self):
        """Test generate_unique_id sanitizes input."""
        from lib.utils.safety import generate_unique_id
        result = generate_unique_id("My-Test Name!", existing_ids=set())
        assert "-" not in result
        assert "!" not in result
        assert " " not in result

    def test_generate_unique_id_custom_separator(self):
        """Test generate_unique_id with custom separator."""
        from lib.utils.safety import generate_unique_id
        # "Test Name" becomes "test_name" after sanitization
        existing = {"test_name"}  # Must match the sanitized base name
        result = generate_unique_id("Test Name", existing_ids=existing, separator='.')
        assert result == "test_name.1"


class TestIdExists:
    """Tests for id_exists function."""

    def test_id_exists_true(self):
        """Test id_exists returns True for existing ID."""
        from lib.utils.safety import id_exists
        existing = {"test_id", "other_id"}
        assert id_exists("test_id", existing) is True

    def test_id_exists_false(self):
        """Test id_exists returns False for non-existing ID."""
        from lib.utils.safety import id_exists
        existing = {"test_id", "other_id"}
        assert id_exists("nonexistent", existing) is False


class TestValidateFilePath:
    """Tests for validate_file_path function."""

    def test_validate_file_path_exists(self):
        """Test validate_file_path with existing file."""
        from lib.utils.safety import validate_file_path
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test")
            tmp_path = tmp.name
        try:
            result = validate_file_path(tmp_path, must_exist=True)
            assert result.exists()
        finally:
            os.unlink(tmp_path)

    def test_validate_file_path_not_exists(self):
        """Test validate_file_path raises for missing file."""
        from lib.utils.safety import validate_file_path
        with pytest.raises(FileNotFoundError):
            validate_file_path("/nonexistent/file.txt", must_exist=True)

    def test_validate_file_path_relative(self):
        """Test validate_file_path rejects relative path."""
        from lib.utils.safety import validate_file_path
        with pytest.raises(ValueError):
            validate_file_path("relative/path.txt", must_exist=False)

    def test_validate_file_path_no_exist_check(self):
        """Test validate_file_path with must_exist=False."""
        from lib.utils.safety import validate_file_path
        result = validate_file_path("/absolute/path.txt", must_exist=False)
        assert result == Path("/absolute/path.txt")


class TestValidateRange:
    """Tests for validate_range function."""

    def test_validate_range_within(self):
        """Test validate_range with value within range."""
        from lib.utils.safety import validate_range
        result = validate_range(5, "test", 0, 10)
        assert result == 5

    def test_validate_range_clamp_below(self):
        """Test validate_range clamps below minimum."""
        from lib.utils.safety import validate_range
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = validate_range(-5, "test", 0, 10)
            assert result == 0
            assert len(w) >= 1

    def test_validate_range_clamp_above(self):
        """Test validate_range clamps above maximum."""
        from lib.utils.safety import validate_range
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = validate_range(15, "test", 0, 10)
            assert result == 10
            assert len(w) >= 1

    def test_validate_range_nan(self):
        """Test validate_range rejects NaN."""
        from lib.utils.safety import validate_range
        with pytest.raises(ValueError):
            validate_range(float('nan'), "test", 0, 10)


class TestNoJsonschema:
    """Tests for behavior when jsonschema is not available."""

    def test_validate_yaml_without_jsonschema(self):
        """Test validate_yaml gracefully handles missing jsonschema."""
        from lib.utils import safety
        original_has = safety.HAS_JSONSCHEMA
        try:
            safety.HAS_JSONSCHEMA = False
            result = safety.validate_yaml({}, 'pose')
            assert result is True  # Returns True when no jsonschema
        finally:
            safety.HAS_JSONSCHEMA = original_has

    def test_validate_yaml_strict_without_jsonschema(self):
        """Test validate_yaml strict mode without jsonschema."""
        from lib.utils import safety
        original_has = safety.HAS_JSONSCHEMA
        try:
            safety.HAS_JSONSCHEMA = False
            with pytest.raises(ImportError):
                safety.validate_yaml({}, 'pose', strict=True)
        finally:
            safety.HAS_JSONSCHEMA = original_has
