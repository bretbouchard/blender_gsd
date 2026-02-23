"""
Tests for review/__init__.py module.

Tests the main exports and module structure.
"""

import pytest


class TestReviewModuleInit:
    """Tests for review module __init__.py."""

    def test_module_imports(self):
        """Test that the review module can be imported."""
        from lib.review import __version__, __all__
        assert __version__ == "1.0.0"
        assert isinstance(__all__, list)

    def test_exports_list(self):
        """Test that __all__ contains expected exports."""
        from lib.review import __all__

        expected = [
            # Enums
            "ValidationLevel",
            "ValidationCategory",
            "ApprovalStatus",
            "ReportFormat",
            # Data classes
            "ValidationResult",
            "ValidationReport",
            "ComparisonResult",
            "ChecklistItem",
            "Checklist",
            "ApprovalRecord",
            # Classes
            "ValidationEngine",
            "ComparisonTool",
            "ChecklistManager",
            "ReportGenerator",
            "ApprovalWorkflow",
            # Functions
            "validate_scene",
            "generate_report",
        ]

        for item in expected:
            assert item in __all__, f"{item} not in __all__"


class TestReviewModuleImports:
    """Test importing specific items from the review module."""

    def test_import_validation_components(self):
        """Test importing validation components."""
        from lib.review import (
            ValidationLevel,
            ValidationCategory,
            ValidationResult,
            ValidationReport,
            ValidationEngine,
            validate_scene,
        )

        assert ValidationLevel is not None
        assert ValidationCategory is not None
        assert ValidationResult is not None
        assert ValidationReport is not None
        assert ValidationEngine is not None
        assert callable(validate_scene)

    def test_import_comparison_components(self):
        """Test importing comparison components."""
        from lib.review import ComparisonResult, ComparisonTool

        assert ComparisonResult is not None
        assert ComparisonTool is not None

    def test_import_checklist_components(self):
        """Test importing checklist components."""
        from lib.review import ChecklistItem, Checklist, ChecklistManager

        assert ChecklistItem is not None
        assert Checklist is not None
        assert ChecklistManager is not None

    def test_import_report_components(self):
        """Test importing report components."""
        from lib.review import ReportFormat, ReportGenerator, generate_report

        assert ReportFormat is not None
        assert ReportGenerator is not None
        assert callable(generate_report)

    def test_import_workflow_components(self):
        """Test importing workflow components."""
        from lib.review import ApprovalStatus, ApprovalRecord, ApprovalWorkflow

        assert ApprovalStatus is not None
        assert ApprovalRecord is not None
        assert ApprovalWorkflow is not None


class TestReviewModuleSubmodules:
    """Test importing submodules directly."""

    def test_import_validation_module(self):
        """Test importing validation module directly."""
        from lib.review.validation import ValidationEngine
        assert ValidationEngine is not None

    def test_import_comparison_module(self):
        """Test importing comparison module directly."""
        from lib.review.comparison import ComparisonTool
        assert ComparisonTool is not None

    def test_import_checklists_module(self):
        """Test importing checklists module directly."""
        from lib.review.checklists import ChecklistManager
        assert ChecklistManager is not None

    def test_import_reports_module(self):
        """Test importing reports module directly."""
        from lib.review.reports import ReportGenerator
        assert ReportGenerator is not None

    def test_import_workflow_module(self):
        """Test importing workflow module directly."""
        from lib.review.workflow import ApprovalWorkflow
        assert ApprovalWorkflow is not None


class TestReviewIntegration:
    """Integration tests for review module components."""

    def test_validation_to_report_workflow(self):
        """Test workflow from validation to report generation."""
        from lib.review import (
            ValidationEngine,
            ReportGenerator,
            generate_report,
        )
        import tempfile
        import os

        # Validate a scene
        engine = ValidationEngine()
        report = engine.validate_scene({
            "objects": [{"name": "Cube", "dimensions": [2, 2, 2]}],
            "lights": [{"name": "Light"}],
        })

        # Generate report
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            result = generate_report(
                report.to_dict(),
                temp_path,
                format="json"
            )
            assert result is True
            assert os.path.exists(temp_path)
        finally:
            os.unlink(temp_path)

    def test_checklist_to_validation_workflow(self):
        """Test workflow from checklist to validation."""
        from lib.review import ChecklistManager, ValidationEngine

        # Create checklist
        manager = ChecklistManager()
        checklist = manager.create_checklist(
            name="Pre-render",
            items=[
                {"item_id": "scale", "name": "Scale Check", "required": True},
                {"item_id": "materials", "name": "Materials Check", "required": True},
            ]
        )

        # Run validation
        engine = ValidationEngine()
        report = engine.validate_scene({
            "objects": [{"name": "Test", "dimensions": [2, 2, 2]}],
            "lights": [{"name": "Light"}],
        })

        # Update checklist based on validation
        if report.is_valid:
            manager.check_item(checklist.checklist_id, "scale", "completed")

        assert checklist.items[0].status == "completed" or report.error_count > 0

    def test_approval_workflow_with_validation(self):
        """Test approval workflow with validation."""
        from lib.review import ApprovalWorkflow, ValidationEngine

        # Create version
        workflow = ApprovalWorkflow()
        version = workflow.create_version("Test Scene", "artist")

        # Run validation
        engine = ValidationEngine()
        report = engine.validate_scene({
            "objects": [{"name": "Test", "dimensions": [2, 2, 2]}],
            "lights": [{"name": "Light"}],
        })

        # Submit for review
        workflow.submit_for_review(
            version.version_id,
            validation_report_id=report.report_id,
        )

        # Approve if valid
        if report.is_valid:
            workflow.approve(version.version_id, "reviewer", "All checks pass")
        else:
            workflow.request_revision(
                version.version_id,
                "reviewer",
                "Fix validation errors",
            )

        assert version.status in ("approved", "revision")
