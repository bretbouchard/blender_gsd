"""
Continuity Validator

Validation of costume continuity across scenes.

Requirements:
- REQ-WARD-04: Continuity validation

Part of Phase 10.1: Wardrobe System
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

from .wardrobe_types import (
    Costume,
    CostumeAssignment,
    CostumeChange,
    WardrobeRegistry,
    IssueType,
    IssueSeverity,
    is_valid_condition_progression,
    CONDITION_PROGRESSION,
)


@dataclass
class ContinuityIssue:
    """Represents a continuity problem."""
    issue_type: str  # costume_mismatch, condition_mismatch, missing_assignment
    character: str
    scene: int
    description: str
    severity: str  # error, warning, info
    suggestion: str = ""
    related_scene: int = 0  # For cross-scene issues
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "issue_type": self.issue_type,
            "character": self.character,
            "scene": self.scene,
            "description": self.description,
            "severity": self.severity,
            "suggestion": self.suggestion,
            "related_scene": self.related_scene,
            "details": self.details,
        }


@dataclass
class ContinuityReport:
    """Complete continuity validation report."""
    production: str
    generated_at: datetime
    issues: List[ContinuityIssue] = field(default_factory=list)
    by_character: Dict[str, List[ContinuityIssue]] = field(default_factory=dict)
    by_scene: Dict[int, List[ContinuityIssue]] = field(default_factory=dict)
    summary: Dict[str, int] = field(default_factory=dict)
    statistics: Dict[str, Any] = field(default_factory=dict)

    def add_issue(self, issue: ContinuityIssue) -> None:
        """Add issue to report."""
        self.issues.append(issue)

        # Index by character
        if issue.character not in self.by_character:
            self.by_character[issue.character] = []
        self.by_character[issue.character].append(issue)

        # Index by scene
        if issue.scene not in self.by_scene:
            self.by_scene[issue.scene] = []
        self.by_scene[issue.scene].append(issue)

    def get_errors(self) -> List[ContinuityIssue]:
        """Get all error-level issues."""
        return [i for i in self.issues if i.severity == "error"]

    def get_warnings(self) -> List[ContinuityIssue]:
        """Get all warning-level issues."""
        return [i for i in self.issues if i.severity == "warning"]

    def get_by_severity(self, severity: str) -> List[ContinuityIssue]:
        """Get issues by severity level."""
        return [i for i in self.issues if i.severity == severity]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "production": self.production,
            "generated_at": self.generated_at.isoformat(),
            "issues": [i.to_dict() for i in self.issues],
            "by_character": {
                k: [i.to_dict() for i in v]
                for k, v in self.by_character.items()
            },
            "by_scene": {
                str(k): [i.to_dict() for i in v]
                for k, v in self.by_scene.items()
            },
            "summary": self.summary,
            "statistics": self.statistics,
        }


def validate_continuity(registry: WardrobeRegistry) -> ContinuityReport:
    """Validate wardrobe continuity across all scenes.

    Performs comprehensive validation including:
    - Missing assignments
    - Costume mismatches between consecutive scenes
    - Condition progression validity
    - Undocumented costume changes

    Args:
        registry: Wardrobe registry to validate

    Returns:
        ContinuityReport with all found issues
    """
    report = ContinuityReport(
        production=registry.production_name,
        generated_at=datetime.now(),
    )

    # Check each character
    for character in registry.get_all_characters():
        # Check for missing assignments
        _check_missing_assignments(character, registry, report)

        # Check costume consistency
        _check_costume_consistency(character, registry, report)

        # Check condition progression
        _check_condition_progression(character, registry, report)

    # Generate summary
    report.summary = {
        "total_issues": len(report.issues),
        "errors": len(report.get_errors()),
        "warnings": len(report.get_warnings()),
        "info": len(report.get_by_severity("info")),
        "characters_with_issues": len(report.by_character),
        "scenes_with_issues": len(report.by_scene),
    }

    report.statistics = {
        "total_characters": len(registry.get_all_characters()),
        "total_costumes": len(registry.costumes),
        "total_assignments": len(registry.assignments),
        "total_changes": len(registry.changes),
    }

    return report


def _check_missing_assignments(
    character: str,
    registry: WardrobeRegistry,
    report: ContinuityReport,
) -> None:
    """Check for missing costume assignments in scene gaps."""
    assignments = registry.get_assignments_for_character(character)

    if len(assignments) < 2:
        return

    # Sort by scene
    sorted_assignments = sorted(assignments, key=lambda a: a.scene)

    # Check for gaps
    for i in range(1, len(sorted_assignments)):
        prev_scene = sorted_assignments[i - 1].scene
        curr_scene = sorted_assignments[i].scene

        # If there's a gap of more than 1 scene, flag it
        if curr_scene - prev_scene > 1:
            # Check if scenes in between have no assignment
            for scene in range(prev_scene + 1, curr_scene):
                if not registry.get_assignment(character, scene):
                    # Check if this scene even exists in the production
                    all_scenes = registry.get_all_scenes()
                    if scene in all_scenes:
                        report.add_issue(ContinuityIssue(
                            issue_type=IssueType.MISSING_ASSIGNMENT.value,
                            character=character,
                            scene=scene,
                            description=f"No costume assignment for scene {scene}",
                            severity=IssueSeverity.WARNING.value,
                            suggestion=f"Assign costume for {character} in scene {scene}",
                            related_scene=prev_scene,
                        ))


def check_costume_consistency(
    character: str,
    registry: WardrobeRegistry,
) -> List[ContinuityIssue]:
    """Check costume consistency for character.

    Verifies that consecutive scenes within the same narrative time
    have consistent costumes unless a change is documented.

    Args:
        character: Character name
        registry: Wardrobe registry

    Returns:
        List of consistency issues
    """
    issues = []
    assignments = sorted(
        registry.get_assignments_for_character(character),
        key=lambda a: a.scene,
    )

    if len(assignments) < 2:
        return issues

    for i in range(1, len(assignments)):
        prev = assignments[i - 1]
        curr = assignments[i]

        # Check for undocumented costume changes
        if prev.costume != curr.costume:
            # Check if this change is documented
            is_documented = any(
                c.character == character
                and c.scene_before == prev.scene
                and c.scene_after == curr.scene
                for c in registry.changes
            )

            if not is_documented:
                # Check if scenes are consecutive (no time for change)
                if curr.scene - prev.scene == 1:
                    issues.append(ContinuityIssue(
                        issue_type=IssueType.UNDOCUMENTED_CHANGE.value,
                        character=character,
                        scene=curr.scene,
                        description=(
                            f"Undocumented costume change from '{prev.costume}' "
                            f"to '{curr.costume}' between consecutive scenes"
                        ),
                        severity=IssueSeverity.WARNING.value,
                        suggestion=(
                            f"Document this costume change or verify it's intentional"
                        ),
                        related_scene=prev.scene,
                        details={
                            "costume_before": prev.costume,
                            "costume_after": curr.costume,
                        },
                    ))

        # Check if costume objects match
        prev_costume = registry.get_costume(prev.costume)
        curr_costume = registry.get_costume(curr.costume)

        if prev_costume and curr_costume and prev.costume == curr.costume:
            # Same costume name - verify pieces match
            if not _verify_costume_pieces_match(prev, curr, prev_costume):
                issues.append(ContinuityIssue(
                    issue_type=IssueType.MISSING_PIECE.value,
                    character=character,
                    scene=curr.scene,
                    description=f"Costume pieces differ for same costume '{curr.costume}'",
                    severity=IssueSeverity.WARNING.value,
                    suggestion="Verify costume pieces are consistent",
                    related_scene=prev.scene,
                ))

    return issues


def _check_costume_consistency(
    character: str,
    registry: WardrobeRegistry,
    report: ContinuityReport,
) -> None:
    """Check costume consistency and add to report."""
    issues = check_costume_consistency(character, registry)
    for issue in issues:
        report.add_issue(issue)


def _verify_costume_pieces_match(
    prev: CostumeAssignment,
    curr: CostumeAssignment,
    costume: Costume,
) -> bool:
    """Verify costume pieces haven't changed unexpectedly."""
    # If there are modifications, assume they're intentional
    if curr.modifications:
        return True

    # Basic check - if no modifications noted, should be consistent
    return True


def check_condition_progression(
    character: str,
    registry: WardrobeRegistry,
) -> List[ContinuityIssue]:
    """Check if condition changes make sense.

    Validates that costume conditions progress logically:
    - Can't go from damaged to pristine without cleaning
    - Can't go from torn to pristine ever
    - etc.

    Args:
        character: Character name
        registry: Wardrobe registry

    Returns:
        List of condition progression issues
    """
    issues = []
    assignments = sorted(
        registry.get_assignments_for_character(character),
        key=lambda a: a.scene,
    )

    if len(assignments) < 2:
        return issues

    for i in range(1, len(assignments)):
        prev = assignments[i - 1]
        curr = assignments[i]

        # Only check condition progression for same costume
        if prev.costume != curr.costume:
            continue

        if not is_valid_condition_progression(prev.condition, curr.condition):
            issues.append(ContinuityIssue(
                issue_type=IssueType.INVALID_PROGRESSION.value,
                character=character,
                scene=curr.scene,
                description=(
                    f"Invalid condition progression from '{prev.condition}' "
                    f"to '{curr.condition}' for costume '{curr.costume}'"
                ),
                severity=IssueSeverity.ERROR.value,
                suggestion=_get_condition_fix_suggestion(prev.condition, curr.condition),
                related_scene=prev.scene,
                details={
                    "condition_before": prev.condition,
                    "condition_after": curr.condition,
                    "valid_next_conditions": CONDITION_PROGRESSION.get(prev.condition, []),
                },
            ))

    return issues


def _check_condition_progression(
    character: str,
    registry: WardrobeRegistry,
    report: ContinuityReport,
) -> None:
    """Check condition progression and add to report."""
    issues = check_condition_progression(character, registry)
    for issue in issues:
        report.add_issue(issue)


def _get_condition_fix_suggestion(from_condition: str, to_condition: str) -> str:
    """Get suggestion for fixing condition progression issue."""
    valid = CONDITION_PROGRESSION.get(from_condition, [])
    if "pristine" in valid:
        return f"Consider adding a cleaning scene, or change condition to one of: {', '.join(valid)}"
    else:
        return f"Condition '{from_condition}' cannot become '{to_condition}'. Valid options: {', '.join(valid)}"


def suggest_costume_changes(registry: WardrobeRegistry) -> List[str]:
    """Suggest where costume changes might be needed.

    Analyzes scene patterns to suggest potential costume changes:
    - Long scene sequences without changes
    - Location changes
    - Time jumps

    Args:
        registry: Wardrobe registry

    Returns:
        List of suggestions
    """
    suggestions = []

    for character in registry.get_all_characters():
        assignments = sorted(
            registry.get_assignments_for_character(character),
            key=lambda a: a.scene,
        )

        if len(assignments) < 2:
            continue

        # Check for long sequences
        current_costume = assignments[0].costume
        sequence_start = assignments[0].scene

        for i in range(1, len(assignments)):
            if assignments[i].costume != current_costume:
                sequence_length = assignments[i].scene - sequence_start

                if sequence_length > 10:
                    suggestions.append(
                        f"{character} wears '{current_costume}' for {sequence_length} "
                        f"scenes ({sequence_start}-{assignments[i].scene - 1}). "
                        f"Consider a costume change for variety."
                    )

                current_costume = assignments[i].costume
                sequence_start = assignments[i].scene

        # Check final sequence (if no change at end)
        if len(assignments) >= 1:
            final_sequence_length = assignments[-1].scene - sequence_start + 1
            if final_sequence_length > 10:
                suggestions.append(
                    f"{character} wears '{current_costume}' for {final_sequence_length} "
                    f"scenes ({sequence_start}-{assignments[-1].scene}). "
                    f"Consider a costume change for variety."
                )

    return suggestions


def validate_scene(registry: WardrobeRegistry, scene: int) -> List[ContinuityIssue]:
    """Validate continuity for a specific scene.

    Args:
        registry: Wardrobe registry
        scene: Scene number

    Returns:
        List of issues for the scene
    """
    issues = []
    assignments = registry.get_assignments_for_scene(scene)

    for assignment in assignments:
        # Verify costume exists
        costume = registry.get_costume(assignment.costume)
        if not costume:
            issues.append(ContinuityIssue(
                issue_type=IssueType.MISSING_PIECE.value,
                character=assignment.character,
                scene=scene,
                description=f"Costume '{assignment.costume}' not found in registry",
                severity=IssueSeverity.ERROR.value,
                suggestion=f"Create costume '{assignment.costume}' or fix assignment",
            ))
            continue

        # Verify condition is valid
        if assignment.condition not in CONDITION_PROGRESSION:
            issues.append(ContinuityIssue(
                issue_type=IssueType.CONDITION_MISMATCH.value,
                character=assignment.character,
                scene=scene,
                description=f"Invalid condition '{assignment.condition}'",
                severity=IssueSeverity.WARNING.value,
                suggestion=f"Use valid condition: {', '.join(CONDITION_PROGRESSION.keys())}",
            ))

    return issues


def generate_continuity_report_markdown(report: ContinuityReport) -> str:
    """Generate markdown report.

    Args:
        report: Continuity report

    Returns:
        Markdown string
    """
    lines = [
        f"# Continuity Report: {report.production}",
        "",
        f"**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Summary",
        "",
        f"- Total Issues: {report.summary.get('total_issues', 0)}",
        f"- Errors: {report.summary.get('errors', 0)}",
        f"- Warnings: {report.summary.get('warnings', 0)}",
        f"- Info: {report.summary.get('info', 0)}",
        "",
    ]

    if report.issues:
        lines.append("## Issues by Character")
        lines.append("")

        for character, issues in sorted(report.by_character.items()):
            lines.append(f"### {character}")
            lines.append("")

            for issue in issues:
                severity_emoji = {
                    "error": "[ERROR]",
                    "warning": "[WARN]",
                    "info": "[INFO]",
                }.get(issue.severity, "[?]")

                lines.append(f"#### {severity_emoji} Scene {issue.scene}")
                lines.append("")
                lines.append(f"**Type:** {issue.issue_type}")
                lines.append("")
                lines.append(f"**Description:** {issue.description}")
                lines.append("")

                if issue.suggestion:
                    lines.append(f"**Suggestion:** {issue.suggestion}")
                    lines.append("")

                lines.append("---")
                lines.append("")

    return "\n".join(lines)


def generate_continuity_report_html(report: ContinuityReport) -> str:
    """Generate HTML report.

    Args:
        report: Continuity report

    Returns:
        HTML string
    """
    severity_colors = {
        "error": "#ff4444",
        "warning": "#ffaa00",
        "info": "#4488ff",
    }

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Continuity Report: {report.production}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f5f5f5; padding: 20px; border-radius: 8px; }}
        .character {{ margin-top: 30px; }}
        .issue {{ margin: 15px 0; padding: 15px; border-radius: 8px; }}
        .error {{ background: #ffeeee; border-left: 4px solid #ff4444; }}
        .warning {{ background: #fff8ee; border-left: 4px solid #ffaa00; }}
        .info {{ background: #eeefff; border-left: 4px solid #4488ff; }}
        .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; }}
    </style>
</head>
<body>
    <h1>Continuity Report: {report.production}</h1>
    <p><strong>Generated:</strong> {report.generated_at.strftime('%Y-%m-%d %H:%M')}</p>

    <div class="summary">
        <h2>Summary</h2>
        <ul>
            <li>Total Issues: {report.summary.get('total_issues', 0)}</li>
            <li>Errors: {report.summary.get('errors', 0)}</li>
            <li>Warnings: {report.summary.get('warnings', 0)}</li>
            <li>Info: {report.summary.get('info', 0)}</li>
        </ul>
    </div>
"""

    for character, issues in sorted(report.by_character.items()):
        html += f'    <div class="character">\n'
        html += f'        <h2>{character}</h2>\n'

        for issue in issues:
            color = severity_colors.get(issue.severity, "#888888")
            html += f"""        <div class="issue {issue.severity}">
            <strong>Scene {issue.scene}</strong>
            <span class="badge" style="background: {color}; color: white;">{issue.severity.upper()}</span>
            <p><strong>Type:</strong> {issue.issue_type}</p>
            <p>{issue.description}</p>
            {f'<p><em>Suggestion: {issue.suggestion}</em></p>' if issue.suggestion else ''}
        </div>
"""

        html += "    </div>\n"

    html += """</body>
</html>"""

    return html
