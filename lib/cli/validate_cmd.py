"""
Validate Command

Validates project structure and configuration.

Usage:
    blender-gsd validate .
    blender-gsd validate tasks/
    blender-gsd validate my-artifact.yaml
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class ValidationIssue:
    """Represents a validation issue."""
    path: str
    message: str
    severity: str  # "error", "warning", "info"
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of validation."""
    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def info(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "info"]


class ValidateCommand:
    """
    Validate project structure and configuration.
    """

    # Required files/directories for a valid project
    REQUIRED_STRUCTURE = [
        "README.md",
    ]

    OPTIONAL_STRUCTURE = [
        "Makefile",
        "tasks/",
        "scripts/",
        ".planning/",
        ".vscode/",
        "configs/",
    ]

    def __init__(self, cli_config=None):
        """Initialize command."""
        self.cli_config = cli_config

    def validate_project(self, project_path: Path) -> ValidationResult:
        """
        Validate entire project structure.

        Args:
            project_path: Path to project root

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult(valid=True)

        # Check project exists
        if not project_path.exists():
            result.valid = False
            result.issues.append(ValidationIssue(
                path=str(project_path),
                message="Project directory does not exist",
                severity="error"
            ))
            return result

        # Check required files
        for required in self.REQUIRED_STRUCTURE:
            required_path = project_path / required
            if not required_path.exists():
                result.valid = False
                result.issues.append(ValidationIssue(
                    path=required,
                    message=f"Required file/directory missing: {required}",
                    severity="error",
                    suggestion=f"Create {required}"
                ))

        # Check optional structure
        for optional in self.OPTIONAL_STRUCTURE:
            optional_path = project_path / optional
            if not optional_path.exists():
                result.issues.append(ValidationIssue(
                    path=optional,
                    message=f"Optional file/directory missing: {optional}",
                    severity="info",
                    suggestion=f"Consider adding {optional} for better project structure"
                ))

        # Validate tasks if present
        tasks_dir = project_path / "tasks"
        if tasks_dir.exists():
            task_result = self.validate_tasks_dir(tasks_dir)
            result.issues.extend(task_result.issues)
            if not task_result.valid:
                result.valid = False

        # Validate scripts if present
        scripts_dir = project_path / "scripts"
        if scripts_dir.exists():
            script_result = self.validate_scripts_dir(scripts_dir)
            result.issues.extend(script_result.issues)
            if not script_result.valid:
                result.valid = False

        # Validate planning structure if present
        planning_dir = project_path / ".planning"
        if planning_dir.exists():
            planning_result = self.validate_planning_dir(planning_dir)
            result.issues.extend(planning_result.issues)

        return result

    def validate_tasks_dir(self, tasks_dir: Path) -> ValidationResult:
        """Validate tasks directory."""
        result = ValidationResult(valid=True)

        task_files = list(tasks_dir.glob("*.yaml"))
        if not task_files:
            result.issues.append(ValidationIssue(
                path="tasks/",
                message="No task files found",
                severity="warning",
                suggestion="Add task YAML files to define artifacts"
            ))
            return result

        for task_file in task_files:
            task_result = self.validate_task_file(task_file)
            result.issues.extend(task_result.issues)
            if not task_result.valid:
                result.valid = False

        return result

    def validate_task_file(self, task_file: Path) -> ValidationResult:
        """Validate a single task file."""
        result = ValidationResult(valid=True)

        try:
            import yaml
            content = yaml.safe_load(task_file.read_text())

            if not content:
                result.valid = False
                result.issues.append(ValidationIssue(
                    path=str(task_file),
                    message="Task file is empty",
                    severity="error"
                ))
                return result

            # Check required fields
            required_fields = ["name", "version"]
            for field in required_fields:
                if field not in content:
                    result.issues.append(ValidationIssue(
                        path=str(task_file),
                        message=f"Missing required field: {field}",
                        severity="warning",
                        suggestion=f"Add '{field}' to task definition"
                    ))

        except Exception as e:
            result.valid = False
            result.issues.append(ValidationIssue(
                path=str(task_file),
                message=f"Failed to parse task file: {e}",
                severity="error"
            ))

        return result

    def validate_scripts_dir(self, scripts_dir: Path) -> ValidationResult:
        """Validate scripts directory."""
        result = ValidationResult(valid=True)

        script_files = list(scripts_dir.glob("*.py"))
        if not script_files:
            result.issues.append(ValidationIssue(
                path="scripts/",
                message="No Python scripts found",
                severity="info",
                suggestion="Add Python scripts to generate artifacts"
            ))
            return result

        for script_file in script_files:
            script_result = self.validate_script_file(script_file)
            result.issues.extend(script_result.issues)

        return result

    def validate_script_file(self, script_file: Path) -> ValidationResult:
        """Validate a single Python script."""
        result = ValidationResult(valid=True)

        try:
            content = script_file.read_text()

            # Basic syntax check
            compile(content, str(script_file), 'exec')

            # Check for main function
            if "def main" not in content and "if __name__" not in content:
                result.issues.append(ValidationIssue(
                    path=str(script_file),
                    message="No main() function or __main__ guard found",
                    severity="info",
                    suggestion="Add a main() function for standalone execution"
                ))

        except SyntaxError as e:
            result.valid = False
            result.issues.append(ValidationIssue(
                path=str(script_file),
                message=f"Syntax error: {e.msg} at line {e.lineno}",
                severity="error"
            ))

        return result

    def validate_planning_dir(self, planning_dir: Path) -> ValidationResult:
        """Validate planning directory structure."""
        result = ValidationResult(valid=True)

        expected_files = ["PROJECT.md", "REQUIREMENTS.md", "ROADMAP.md"]
        for expected in expected_files:
            expected_path = planning_dir / expected
            if not expected_path.exists():
                result.issues.append(ValidationIssue(
                    path=f".planning/{expected}",
                    message=f"Planning file missing: {expected}",
                    severity="info",
                    suggestion=f"Create {expected} for GSD workflow"
                ))

        return result

    def format_result(self, result: ValidationResult, verbose: bool = False) -> str:
        """
        Format validation result for display.

        Args:
            result: Validation result
            verbose: Include info-level issues

        Returns:
            Formatted string
        """
        output = []

        status = "VALID" if result.valid else "INVALID"
        output.append(f"Status: {status}")
        output.append(f"Errors: {len(result.errors)}")
        output.append(f"Warnings: {len(result.warnings)}")
        if verbose:
            output.append(f"Info: {len(result.info)}")
        output.append("")

        if result.errors:
            output.append("Errors:")
            for error in result.errors:
                output.append(f"  [ERROR] {error.path}: {error.message}")
                if error.suggestion:
                    output.append(f"          Suggestion: {error.suggestion}")
            output.append("")

        if result.warnings:
            output.append("Warnings:")
            for warning in result.warnings:
                output.append(f"  [WARNING] {warning.path}: {warning.message}")
                if warning.suggestion:
                    output.append(f"            Suggestion: {warning.suggestion}")
            output.append("")

        if verbose and result.info:
            output.append("Info:")
            for info in result.info:
                output.append(f"  [INFO] {info.path}: {info.message}")
                if info.suggestion:
                    output.append(f"         Suggestion: {info.suggestion}")
            output.append("")

        return "\n".join(output)
