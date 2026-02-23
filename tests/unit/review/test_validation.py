"""
Tests for validation module.

Tests run WITHOUT Blender (bpy) by testing only non-Blender-dependent code paths.
"""

import pytest
from datetime import datetime


class TestValidationLevel:
    """Tests for ValidationLevel enum."""

    def test_level_values(self):
        """Test ValidationLevel enum values."""
        from lib.review.validation import ValidationLevel

        assert ValidationLevel.ERROR.value == "error"
        assert ValidationLevel.WARNING.value == "warning"
        assert ValidationLevel.INFO.value == "info"
        assert ValidationLevel.PASS.value == "pass"


class TestValidationCategory:
    """Tests for ValidationCategory enum."""

    def test_category_values(self):
        """Test ValidationCategory enum values."""
        from lib.review.validation import ValidationCategory

        assert ValidationCategory.SCALE.value == "scale"
        assert ValidationCategory.MATERIALS.value == "materials"
        assert ValidationCategory.LIGHTING.value == "lighting"
        assert ValidationCategory.GEOMETRY.value == "geometry"
        assert ValidationCategory.NAMING.value == "naming"
        assert ValidationCategory.PERFORMANCE.value == "performance"
        assert ValidationCategory.RENDER.value == "render"
        assert ValidationCategory.COMPOSITION.value == "composition"


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_result_creation(self):
        """Test creating a ValidationResult."""
        from lib.review.validation import ValidationResult

        result = ValidationResult(
            check_id="scale_001",
            category="scale",
            level="pass",
            message="Scale is correct",
        )

        assert result.check_id == "scale_001"
        assert result.category == "scale"
        assert result.level == "pass"
        assert result.message == "Scale is correct"

    def test_result_defaults(self):
        """Test ValidationResult default values."""
        from lib.review.validation import ValidationResult

        result = ValidationResult()
        assert result.check_id == ""
        assert result.category == "geometry"
        assert result.level == "pass"
        assert result.message == ""
        assert result.auto_fix_available is False

    def test_result_to_dict(self):
        """Test ValidationResult serialization."""
        from lib.review.validation import ValidationResult

        result = ValidationResult(
            check_id="test_001",
            category="materials",
            level="warning",
            message="Test warning",
            actual_value=150,
            expected_value="<= 100",
        )
        data = result.to_dict()

        assert data["check_id"] == "test_001"
        assert data["category"] == "materials"
        assert data["level"] == "warning"
        assert data["actual_value"] == 150

    def test_result_from_dict(self):
        """Test ValidationResult deserialization."""
        from lib.review.validation import ValidationResult

        data = {
            "check_id": "test_001",
            "category": "scale",
            "level": "error",
            "message": "Bad scale",
            "auto_fix_available": True,
        }
        result = ValidationResult.from_dict(data)

        assert result.check_id == "test_001"
        assert result.level == "error"
        assert result.auto_fix_available is True


class TestValidationReport:
    """Tests for ValidationReport dataclass."""

    def test_report_creation(self):
        """Test creating a ValidationReport."""
        from lib.review.validation import ValidationReport, ValidationResult

        results = [
            ValidationResult(level="pass", message="OK"),
            ValidationResult(level="error", message="Bad"),
        ]

        report = ValidationReport(
            report_id="report_001",
            scene_name="Test Scene",
            results=results,
        )

        assert report.report_id == "report_001"
        assert report.scene_name == "Test Scene"
        assert len(report.results) == 2

    def test_report_pass_count(self):
        """Test pass_count property."""
        from lib.review.validation import ValidationReport, ValidationResult

        report = ValidationReport(results=[
            ValidationResult(level="pass"),
            ValidationResult(level="pass"),
            ValidationResult(level="error"),
        ])

        assert report.pass_count == 2

    def test_report_error_count(self):
        """Test error_count property."""
        from lib.review.validation import ValidationReport, ValidationResult

        report = ValidationReport(results=[
            ValidationResult(level="error"),
            ValidationResult(level="error"),
            ValidationResult(level="warning"),
        ])

        assert report.error_count == 2

    def test_report_warning_count(self):
        """Test warning_count property."""
        from lib.review.validation import ValidationReport, ValidationResult

        report = ValidationReport(results=[
            ValidationResult(level="warning"),
            ValidationResult(level="warning"),
            ValidationResult(level="warning"),
        ])

        assert report.warning_count == 3

    def test_report_info_count(self):
        """Test info_count property."""
        from lib.review.validation import ValidationReport, ValidationResult

        report = ValidationReport(results=[
            ValidationResult(level="info"),
            ValidationResult(level="info"),
        ])

        assert report.info_count == 2

    def test_report_is_valid(self):
        """Test is_valid property."""
        from lib.review.validation import ValidationReport, ValidationResult

        # Valid - no errors
        report1 = ValidationReport(results=[
            ValidationResult(level="pass"),
            ValidationResult(level="warning"),
        ])
        assert report1.is_valid is True

        # Invalid - has errors
        report2 = ValidationReport(results=[
            ValidationResult(level="pass"),
            ValidationResult(level="error"),
        ])
        assert report2.is_valid is False

    def test_report_to_dict(self):
        """Test ValidationReport serialization."""
        from lib.review.validation import ValidationReport, ValidationResult

        report = ValidationReport(
            report_id="report_001",
            scene_name="Test",
            results=[ValidationResult(check_id="1")],
            summary={"total": 1},
        )
        data = report.to_dict()

        assert data["report_id"] == "report_001"
        assert data["scene_name"] == "Test"
        assert len(data["results"]) == 1

    def test_report_from_dict(self):
        """Test ValidationReport deserialization."""
        from lib.review.validation import ValidationReport

        data = {
            "report_id": "report_001",
            "scene_name": "Test Scene",
            "timestamp": "2024-01-01T00:00:00",
            "results": [
                {"check_id": "1", "level": "pass", "message": "OK"},
            ],
            "summary": {"total": 1, "pass": 1, "error": 0, "warning": 0},
        }
        report = ValidationReport.from_dict(data)

        assert report.report_id == "report_001"
        assert len(report.results) == 1


class TestValidationEngine:
    """Tests for ValidationEngine class."""

    def test_engine_creation(self):
        """Test creating a ValidationEngine."""
        from lib.review.validation import ValidationEngine

        engine = ValidationEngine()
        assert engine is not None
        assert engine.config is not None

    def test_engine_with_custom_config(self):
        """Test creating engine with custom config."""
        from lib.review.validation import ValidationEngine

        custom_config = {
            "scale": {"min_object_size": 0.01, "max_object_size": 500},
        }
        engine = ValidationEngine(config=custom_config)

        assert engine.config["scale"]["min_object_size"] == 0.01

    def test_engine_default_checks_registered(self):
        """Test that default checks are registered."""
        from lib.review.validation import ValidationEngine

        engine = ValidationEngine()

        # Should have default checks
        assert "scale_range" in engine._checks
        assert "material_count" in engine._checks
        assert "lighting_basic" in engine._checks
        assert "geometry_polycount" in engine._checks
        assert "naming_convention" in engine._checks

    def test_register_check(self):
        """Test registering a custom check."""
        from lib.review.validation import ValidationEngine, ValidationResult

        engine = ValidationEngine()

        def custom_check(scene_data):
            return [ValidationResult(
                check_id="custom",
                level="pass",
                message="Custom check passed",
            )]

        engine.register_check("custom_check", custom_check)
        assert "custom_check" in engine._checks

    def test_unregister_check(self):
        """Test unregistering a check."""
        from lib.review.validation import ValidationEngine

        engine = ValidationEngine()
        engine.unregister_check("scale_range")

        assert "scale_range" not in engine._checks

    def test_unregister_nonexistent_check(self):
        """Test unregistering a nonexistent check."""
        from lib.review.validation import ValidationEngine

        engine = ValidationEngine()
        result = engine.unregister_check("nonexistent")

        assert result is False

    def test_validate_scene_empty(self):
        """Test validating empty scene."""
        from lib.review.validation import ValidationEngine

        engine = ValidationEngine()
        report = engine.validate_scene({}, scene_name="Empty Scene")

        assert report.scene_name == "Empty Scene"
        assert report.report_id.startswith("val_")

    def test_validate_scene_with_objects(self):
        """Test validating scene with objects."""
        from lib.review.validation import ValidationEngine

        engine = ValidationEngine()
        scene_data = {
            "objects": [
                {"name": "Cube", "dimensions": [2, 2, 2]},
                {"name": "Sphere", "dimensions": [1, 1, 1]},
            ],
            "materials": [{"name": "Material"}],
            "lights": [{"name": "Light"}],
            "total_polygons": 1000,
        }

        report = engine.validate_scene(scene_data, scene_name="Test Scene")

        assert report.scene_name == "Test Scene"
        assert len(report.results) > 0
        assert "total" in report.summary

    def test_validate_scene_specific_checks(self):
        """Test running specific checks."""
        from lib.review.validation import ValidationEngine

        engine = ValidationEngine()
        scene_data = {
            "objects": [{"name": "Cube", "dimensions": [2, 2, 2]}],
        }

        report = engine.validate_scene(
            scene_data,
            checks=["scale_range"],  # Only run scale check
        )

        # All results should be from scale_range
        for result in report.results:
            assert result.check_id == "scale_range"

    def test_check_scale_range_too_small(self):
        """Test scale check with too small object."""
        from lib.review.validation import ValidationEngine

        engine = ValidationEngine()
        scene_data = {
            "objects": [{"name": "Tiny", "dimensions": [0.0001, 0.0001, 0.0001]}],
        }

        results = engine._check_scale_range(scene_data)

        assert len(results) == 1
        assert results[0].level == "warning"
        assert "small" in results[0].message.lower()

    def test_check_scale_range_too_large(self):
        """Test scale check with too large object."""
        from lib.review.validation import ValidationEngine

        engine = ValidationEngine()
        scene_data = {
            "objects": [{"name": "Huge", "dimensions": [2000, 2000, 2000]}],
        }

        results = engine._check_scale_range(scene_data)

        assert len(results) == 1
        assert results[0].level == "warning"
        assert "large" in results[0].message.lower()

    def test_check_scale_range_ok(self):
        """Test scale check with valid object."""
        from lib.review.validation import ValidationEngine

        engine = ValidationEngine()
        scene_data = {
            "objects": [{"name": "Normal", "dimensions": [2, 2, 2]}],
        }

        results = engine._check_scale_range(scene_data)

        assert len(results) == 1
        assert results[0].level == "pass"

    def test_check_material_count_ok(self):
        """Test material count check with OK count."""
        from lib.review.validation import ValidationEngine

        engine = ValidationEngine()
        scene_data = {"materials": [{"name": f"Mat{i}"} for i in range(10)]}

        results = engine._check_material_count(scene_data)

        assert len(results) == 1
        assert results[0].level == "pass"

    def test_check_material_count_too_many(self):
        """Test material count check with too many materials."""
        from lib.review.validation import ValidationEngine

        engine = ValidationEngine()
        scene_data = {"materials": [{"name": f"Mat{i}"} for i in range(150)]}

        results = engine._check_material_count(scene_data)

        assert len(results) == 1
        assert results[0].level == "warning"

    def test_check_lighting_no_lights(self):
        """Test lighting check with no lights."""
        from lib.review.validation import ValidationEngine

        engine = ValidationEngine()
        scene_data = {"lights": []}

        results = engine._check_lighting(scene_data)

        assert len(results) == 1
        assert results[0].level == "error"
        assert "no lights" in results[0].message.lower()

    def test_check_lighting_ok(self):
        """Test lighting check with lights."""
        from lib.review.validation import ValidationEngine

        engine = ValidationEngine()
        scene_data = {"lights": [{"name": "Light"}]}

        results = engine._check_lighting(scene_data)

        assert len(results) == 1
        assert results[0].level == "pass"

    def test_check_lighting_too_many(self):
        """Test lighting check with too many lights."""
        from lib.review.validation import ValidationEngine

        engine = ValidationEngine()
        scene_data = {"lights": [{"name": f"Light{i}"} for i in range(60)]}

        results = engine._check_lighting(scene_data)

        assert len(results) == 1
        assert results[0].level == "warning"

    def test_check_polycount_ok(self):
        """Test polycount check with OK count."""
        from lib.review.validation import ValidationEngine

        engine = ValidationEngine()
        scene_data = {"total_polygons": 100000}

        results = engine._check_polycount(scene_data)

        assert len(results) == 1
        assert results[0].level == "pass"

    def test_check_polycount_high(self):
        """Test polycount check with high count."""
        from lib.review.validation import ValidationEngine

        engine = ValidationEngine()
        scene_data = {"total_polygons": 15000000}

        results = engine._check_polycount(scene_data)

        assert len(results) == 1
        assert results[0].level == "warning"

    def test_check_naming_with_dot(self):
        """Test naming check with dot prefix."""
        from lib.review.validation import ValidationEngine

        engine = ValidationEngine()
        scene_data = {"objects": [{"name": ".Hidden"}]}

        results = engine._check_naming(scene_data)

        assert len(results) == 1
        assert results[0].level == "info"
        assert "dot" in results[0].message.lower()

    def test_check_naming_with_spaces(self):
        """Test naming check with spaces."""
        from lib.review.validation import ValidationEngine

        engine = ValidationEngine()
        scene_data = {"objects": [{"name": "My Object"}]}

        results = engine._check_naming(scene_data)

        assert len(results) == 1
        assert results[0].level == "info"
        assert "space" in results[0].message.lower()

    def test_check_naming_ok(self):
        """Test naming check with valid name."""
        from lib.review.validation import ValidationEngine

        engine = ValidationEngine()
        scene_data = {"objects": [{"name": "My_Object"}]}

        results = engine._check_naming(scene_data)

        assert len(results) == 1
        assert results[0].level == "pass"

    def test_set_threshold(self):
        """Test setting a threshold."""
        from lib.review.validation import ValidationEngine

        engine = ValidationEngine()
        engine.set_threshold("scale", "min_object_size", 0.5)

        assert engine.config["scale"]["min_object_size"] == 0.5

    def test_set_threshold_new_category(self):
        """Test setting threshold in new category."""
        from lib.review.validation import ValidationEngine

        engine = ValidationEngine()
        engine.set_threshold("custom", "value", 100)

        assert engine.config["custom"]["value"] == 100

    def test_get_threshold(self):
        """Test getting a threshold."""
        from lib.review.validation import ValidationEngine

        engine = ValidationEngine()
        # First set a value, then retrieve it
        engine.set_threshold("scale", "min_object_size", 0.5)
        value = engine.get_threshold("scale", "min_object_size")

        assert value == 0.5

    def test_get_threshold_default(self):
        """Test getting threshold with default."""
        from lib.review.validation import ValidationEngine

        engine = ValidationEngine()
        value = engine.get_threshold("nonexistent", "key", default=999)

        assert value == 999

    def test_check_with_exception(self):
        """Test check that raises exception."""
        from lib.review.validation import ValidationEngine, ValidationResult

        engine = ValidationEngine()

        def bad_check(scene_data):
            raise RuntimeError("Check failed!")

        engine.register_check("bad_check", bad_check)

        report = engine.validate_scene({}, checks=["bad_check"])

        # Should contain error result
        assert len(report.results) == 1
        assert report.results[0].level == "error"
        assert "failed" in report.results[0].message.lower()


class TestValidateSceneFunction:
    """Tests for validate_scene convenience function."""

    def test_validate_scene_function(self):
        """Test validate_scene convenience function."""
        from lib.review.validation import validate_scene

        scene_data = {
            "objects": [{"name": "Cube", "dimensions": [2, 2, 2]}],
            "lights": [{"name": "Light"}],
        }

        report = validate_scene(scene_data)

        assert report is not None
        assert report.report_id.startswith("val_")

    def test_validate_scene_with_config(self):
        """Test validate_scene with custom config."""
        from lib.review.validation import validate_scene

        config = {"scale": {"min_object_size": 0.1}}
        scene_data = {"objects": [{"name": "Test", "dimensions": [1, 1, 1]}]}

        report = validate_scene(scene_data, config=config)

        assert report is not None


class TestValidationThresholds:
    """Tests for VALIDATION_THRESHOLDS constant."""

    def test_thresholds_structure(self):
        """Test VALIDATION_THRESHOLDS structure."""
        from lib.review.validation import VALIDATION_THRESHOLDS

        assert "scale" in VALIDATION_THRESHOLDS
        assert "materials" in VALIDATION_THRESHOLDS
        assert "lighting" in VALIDATION_THRESHOLDS
        assert "geometry" in VALIDATION_THRESHOLDS
        assert "performance" in VALIDATION_THRESHOLDS

    def test_scale_thresholds(self):
        """Test scale thresholds."""
        from lib.review.validation import VALIDATION_THRESHOLDS

        scale = VALIDATION_THRESHOLDS["scale"]
        assert "min_object_size" in scale
        assert "max_object_size" in scale

    def test_material_thresholds(self):
        """Test material thresholds."""
        from lib.review.validation import VALIDATION_THRESHOLDS

        materials = VALIDATION_THRESHOLDS["materials"]
        assert "max_material_count" in materials
