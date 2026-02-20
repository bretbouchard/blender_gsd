"""
Tests for Wardrobe System - Continuity Validator

Tests for continuity_validator.py.
"""

import pytest
from datetime import datetime

from lib.character.wardrobe_types import (
    Costume,
    CostumePiece,
    CostumeAssignment,
    CostumeChange,
    WardrobeRegistry,
)
from lib.character.continuity_validator import (
    ContinuityIssue,
    ContinuityReport,
    validate_continuity,
    check_costume_consistency,
    check_condition_progression,
    suggest_costume_changes,
    validate_scene,
    generate_continuity_report_markdown,
    generate_continuity_report_html,
    IssueType,
    IssueSeverity,
)


@pytest.fixture
def registry_with_assignments():
    """Create a registry with sample assignments."""
    registry = WardrobeRegistry(production_name="Test Production")

    # Add costumes
    registry.add_costume(Costume(
        name="hero_casual",
        character="Hero",
        pieces=[
            CostumePiece(name="Shirt", category="top", color="blue", material="cotton"),
        ],
        colors=["blue"],
    ))
    registry.add_costume(Costume(
        name="hero_formal",
        character="Hero",
        pieces=[
            CostumePiece(name="Suit", category="outerwear", color="black", material="wool"),
        ],
        colors=["black"],
    ))

    # Add assignments
    registry.add_assignment(CostumeAssignment(
        character="Hero",
        scene=1,
        costume="hero_casual",
        condition="pristine",
    ))
    registry.add_assignment(CostumeAssignment(
        character="Hero",
        scene=2,
        costume="hero_casual",
        condition="pristine",
    ))
    registry.add_assignment(CostumeAssignment(
        character="Hero",
        scene=5,
        costume="hero_formal",
        condition="pristine",
    ))

    return registry


class TestContinuityIssue:
    """Tests for ContinuityIssue dataclass."""

    def test_create_issue(self):
        """Test creating a continuity issue."""
        issue = ContinuityIssue(
            issue_type="costume_mismatch",
            character="Hero",
            scene=5,
            description="Costume changed without documentation",
            severity="error",
        )
        assert issue.issue_type == "costume_mismatch"
        assert issue.character == "Hero"
        assert issue.severity == "error"

    def test_issue_to_dict(self):
        """Test converting issue to dictionary."""
        issue = ContinuityIssue(
            issue_type="missing_assignment",
            character="Hero",
            scene=3,
            description="No costume assigned",
            severity="warning",
            suggestion="Assign costume",
        )
        data = issue.to_dict()
        assert data["issue_type"] == "missing_assignment"
        assert data["suggestion"] == "Assign costume"


class TestContinuityReport:
    """Tests for ContinuityReport dataclass."""

    def test_create_report(self):
        """Test creating a continuity report."""
        report = ContinuityReport(
            production="Test Production",
            generated_at=datetime.now(),
        )
        assert report.production == "Test Production"
        assert len(report.issues) == 0

    def test_add_issue(self):
        """Test adding issues to report."""
        report = ContinuityReport(
            production="Test",
            generated_at=datetime.now(),
        )
        issue = ContinuityIssue(
            issue_type="error",
            character="Hero",
            scene=1,
            description="Test issue",
            severity="error",
        )
        report.add_issue(issue)

        assert len(report.issues) == 1
        assert "Hero" in report.by_character
        assert 1 in report.by_scene

    def test_get_errors(self):
        """Test getting error-level issues."""
        report = ContinuityReport(
            production="Test",
            generated_at=datetime.now(),
        )
        report.add_issue(ContinuityIssue(
            issue_type="error", character="A", scene=1,
            description="Error", severity="error"
        ))
        report.add_issue(ContinuityIssue(
            issue_type="warning", character="B", scene=2,
            description="Warning", severity="warning"
        ))

        errors = report.get_errors()
        assert len(errors) == 1

    def test_get_warnings(self):
        """Test getting warning-level issues."""
        report = ContinuityReport(
            production="Test",
            generated_at=datetime.now(),
        )
        report.add_issue(ContinuityIssue(
            issue_type="error", character="A", scene=1,
            description="Error", severity="error"
        ))
        report.add_issue(ContinuityIssue(
            issue_type="warning", character="B", scene=2,
            description="Warning", severity="warning"
        ))

        warnings = report.get_warnings()
        assert len(warnings) == 1


class TestValidateContinuity:
    """Tests for validate_continuity function."""

    def test_validate_clean_registry(self, registry_with_assignments):
        """Test validation of registry with no issues."""
        # Document the change
        registry_with_assignments.add_change(CostumeChange(
            character="Hero",
            scene_before=2,
            scene_after=5,
            costume_before="hero_casual",
            costume_after="hero_formal",
        ))

        report = validate_continuity(registry_with_assignments)
        # Should have no errors, but may have info-level items
        assert len(report.get_errors()) == 0

    def test_validate_detects_invalid_condition(self, registry_with_assignments):
        """Test validation detects invalid condition progression."""
        # Add assignment with invalid condition progression
        registry_with_assignments.add_assignment(CostumeAssignment(
            character="Hero",
            scene=6,
            costume="hero_formal",
            condition="pristine",  # Invalid: going from damaged to pristine
        ))
        # First mark the formal as damaged
        for a in registry_with_assignments.assignments:
            if a.scene == 5 and a.costume == "hero_formal":
                a.condition = "damaged"

        report = validate_continuity(registry_with_assignments)
        errors = report.get_errors()

        # Should detect invalid progression
        assert len(errors) > 0
        assert any(e.issue_type == "invalid_progression" for e in errors)


class TestCheckCostumeConsistency:
    """Tests for check_costume_consistency function."""

    def test_no_issues_consistent_costumes(self, registry_with_assignments):
        """Test no issues when costumes are consistent."""
        issues = check_costume_consistency("Hero", registry_with_assignments)
        # No undocumented changes between consecutive scenes
        assert len(issues) == 0

    def test_detects_undocumented_change(self):
        """Test detection of undocumented costume change."""
        registry = WardrobeRegistry()
        registry.add_costume(Costume(
            name="casual",
            character="Hero",
            pieces=[CostumePiece(name="Shirt", category="top", color="blue", material="cotton")],
        ))
        registry.add_costume(Costume(
            name="formal",
            character="Hero",
            pieces=[CostumePiece(name="Suit", category="outerwear", color="black", material="wool")],
        ))
        # Consecutive scenes with different costumes, no documented change
        registry.add_assignment(CostumeAssignment(
            character="Hero", scene=1, costume="casual"
        ))
        registry.add_assignment(CostumeAssignment(
            character="Hero", scene=2, costume="formal"
        ))

        issues = check_costume_consistency("Hero", registry)
        assert len(issues) == 1
        assert issues[0].issue_type == "undocumented_change"


class TestCheckConditionProgression:
    """Tests for check_condition_progression function."""

    def test_valid_progression(self):
        """Test valid condition progression."""
        registry = WardrobeRegistry()
        registry.add_costume(Costume(
            name="test",
            character="Hero",
            pieces=[CostumePiece(name="Shirt", category="top", color="blue", material="cotton")],
        ))
        registry.add_assignment(CostumeAssignment(
            character="Hero", scene=1, costume="test", condition="pristine"
        ))
        registry.add_assignment(CostumeAssignment(
            character="Hero", scene=2, costume="test", condition="worn"
        ))

        issues = check_condition_progression("Hero", registry)
        assert len(issues) == 0

    def test_invalid_progression_damaged_to_pristine(self):
        """Test invalid progression from damaged to pristine."""
        registry = WardrobeRegistry()
        registry.add_costume(Costume(
            name="test",
            character="Hero",
            pieces=[CostumePiece(name="Shirt", category="top", color="blue", material="cotton")],
        ))
        registry.add_assignment(CostumeAssignment(
            character="Hero", scene=1, costume="test", condition="damaged"
        ))
        registry.add_assignment(CostumeAssignment(
            character="Hero", scene=2, costume="test", condition="pristine"
        ))

        issues = check_condition_progression("Hero", registry)
        assert len(issues) == 1
        assert issues[0].issue_type == "invalid_progression"
        assert issues[0].severity == "error"

    def test_different_costumes_no_check(self):
        """Test no condition check when costumes differ."""
        registry = WardrobeRegistry()
        registry.add_costume(Costume(
            name="casual",
            character="Hero",
            pieces=[CostumePiece(name="Shirt", category="top", color="blue", material="cotton")],
        ))
        registry.add_costume(Costume(
            name="formal",
            character="Hero",
            pieces=[CostumePiece(name="Suit", category="outerwear", color="black", material="wool")],
        ))
        registry.add_assignment(CostumeAssignment(
            character="Hero", scene=1, costume="casual", condition="damaged"
        ))
        registry.add_assignment(CostumeAssignment(
            character="Hero", scene=2, costume="formal", condition="pristine"
        ))

        issues = check_condition_progression("Hero", registry)
        # No issues because different costumes
        assert len(issues) == 0


class TestSuggestCostumeChanges:
    """Tests for suggest_costume_changes function."""

    def test_suggest_change_for_long_sequence(self):
        """Test suggestion for long costume sequence."""
        registry = WardrobeRegistry()
        registry.add_costume(Costume(
            name="casual",
            character="Hero",
            pieces=[CostumePiece(name="Shirt", category="top", color="blue", material="cotton")],
        ))

        # 15 scenes with same costume
        for i in range(1, 16):
            registry.add_assignment(CostumeAssignment(
                character="Hero", scene=i, costume="casual"
            ))

        suggestions = suggest_costume_changes(registry)
        assert len(suggestions) == 1
        assert "15 scenes" in suggestions[0]

    def test_no_suggestion_for_short_sequence(self):
        """Test no suggestion for short sequences."""
        registry = WardrobeRegistry()
        registry.add_costume(Costume(
            name="casual",
            character="Hero",
            pieces=[CostumePiece(name="Shirt", category="top", color="blue", material="cotton")],
        ))

        for i in range(1, 6):
            registry.add_assignment(CostumeAssignment(
                character="Hero", scene=i, costume="casual"
            ))

        suggestions = suggest_costume_changes(registry)
        assert len(suggestions) == 0


class TestValidateScene:
    """Tests for validate_scene function."""

    def test_validate_scene_valid(self, registry_with_assignments):
        """Test validation of a valid scene."""
        issues = validate_scene(registry_with_assignments, 1)
        assert len(issues) == 0

    def test_validate_scene_missing_costume(self):
        """Test validation detects missing costume reference."""
        registry = WardrobeRegistry()
        registry.add_assignment(CostumeAssignment(
            character="Hero", scene=1, costume="nonexistent"
        ))

        issues = validate_scene(registry, 1)
        assert len(issues) == 1
        assert issues[0].issue_type == "missing_piece"


class TestReportGeneration:
    """Tests for report generation functions."""

    def test_generate_markdown_report(self):
        """Test markdown report generation."""
        report = ContinuityReport(
            production="Test Production",
            generated_at=datetime.now(),
            summary={"total_issues": 1, "errors": 0, "warnings": 1, "info": 0},
        )
        report.add_issue(ContinuityIssue(
            issue_type="test",
            character="Hero",
            scene=1,
            description="Test issue",
            severity="warning",
        ))

        markdown = generate_continuity_report_markdown(report)
        assert "# Continuity Report" in markdown
        assert "Test Production" in markdown
        assert "Hero" in markdown

    def test_generate_html_report(self):
        """Test HTML report generation."""
        report = ContinuityReport(
            production="Test Production",
            generated_at=datetime.now(),
            summary={"total_issues": 1, "errors": 0, "warnings": 1, "info": 0},
        )
        report.add_issue(ContinuityIssue(
            issue_type="test",
            character="Hero",
            scene=1,
            description="Test issue",
            severity="warning",
        ))

        html = generate_continuity_report_html(report)
        assert "<!DOCTYPE html>" in html
        assert "Test Production" in html
        assert "Hero" in html

    def test_report_to_dict(self):
        """Test report serialization."""
        report = ContinuityReport(
            production="Test",
            generated_at=datetime.now(),
        )
        report.add_issue(ContinuityIssue(
            issue_type="test",
            character="Hero",
            scene=1,
            description="Test",
            severity="error",
        ))

        data = report.to_dict()
        assert data["production"] == "Test"
        assert len(data["issues"]) == 1
        assert "Hero" in data["by_character"]
