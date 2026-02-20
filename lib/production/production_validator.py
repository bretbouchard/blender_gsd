"""
Production Validator

Validate production configurations before execution.

Requirements:
- REQ-ORCH-02: Validate production before execution
- Dependency checking
- Timeline validation

Part of Phase 14.1: Production Orchestrator
"""

from __future__ import annotations
import os
from typing import List, Dict, Any, Optional

from .production_types import (
    ProductionConfig,
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
    CharacterConfig,
    LocationConfig,
    ShotConfig,
    OutputFormat,
)


def validate_production(config: ProductionConfig) -> ValidationResult:
    """
    Complete production validation.

    Runs all validation checks and aggregates results.

    Args:
        config: Production configuration

    Returns:
        ValidationResult with all issues
    """
    result = ValidationResult(valid=True)

    # Run all validation checks
    issues = []
    issues.extend(validate_meta(config))
    issues.extend(validate_characters(config))
    issues.extend(validate_locations(config))
    issues.extend(validate_shots(config))
    issues.extend(validate_dependencies(config))
    issues.extend(validate_timeline(config))
    issues.extend(validate_outputs(config))

    # Add all issues
    for issue in issues:
        if issue.severity == ValidationSeverity.ERROR.value:
            result.add_error(issue.path, issue.message, issue.suggestion)
        elif issue.severity == ValidationSeverity.WARNING.value:
            result.add_warning(issue.path, issue.message, issue.suggestion)
        else:
            result.issues.append(issue)

    return result


def validate_meta(config: ProductionConfig) -> List[ValidationIssue]:
    """
    Validate production metadata.

    Args:
        config: Production configuration

    Returns:
        List of validation issues
    """
    issues = []

    # Check title
    if not config.meta.title:
        issues.append(ValidationIssue(
            path="meta.title",
            severity=ValidationSeverity.WARNING.value,
            message="Production title is empty",
            suggestion="Set a descriptive title for the production",
        ))

    # Check author
    if not config.meta.author:
        issues.append(ValidationIssue(
            path="meta.author",
            severity=ValidationSeverity.INFO.value,
            message="Author not specified",
            suggestion="Add author information for attribution",
        ))

    return issues


def validate_characters(config: ProductionConfig) -> List[ValidationIssue]:
    """
    Validate character configurations.

    Args:
        config: Production configuration

    Returns:
        List of validation issues
    """
    issues = []

    # Check for characters
    if not config.characters:
        issues.append(ValidationIssue(
            path="characters",
            severity=ValidationSeverity.INFO.value,
            message="No characters defined",
            suggestion="Add character configurations for character-based shots",
        ))
        return issues

    for name, char in config.characters.items():
        issues.extend(_validate_character(name, char, config))

    return issues


def _validate_character(name: str, char: CharacterConfig, config: ProductionConfig) -> List[ValidationIssue]:
    """Validate single character."""
    issues = []

    # Check name matches key
    if char.name and char.name != name:
        issues.append(ValidationIssue(
            path=f"characters.{name}.name",
            severity=ValidationSeverity.WARNING.value,
            message=f"Character name '{char.name}' does not match key '{name}'",
            suggestion="Ensure character name matches the dictionary key",
        ))

    # Check model path
    if char.model:
        full_path = _resolve_path(char.model, config.base_path)
        if not os.path.exists(full_path):
            issues.append(ValidationIssue(
                path=f"characters.{name}.model",
                severity=ValidationSeverity.ERROR.value,
                message=f"Character model file not found: {char.model}",
                suggestion="Verify the model file path exists",
            ))

    # Check wardrobe assignments
    for range_key, costume in char.wardrobe_assignments.items():
        if not _is_valid_scene_range(range_key):
            issues.append(ValidationIssue(
                path=f"characters.{name}.wardrobe_assignments.{range_key}",
                severity=ValidationSeverity.WARNING.value,
                message=f"Invalid scene range format: {range_key}",
                suggestion="Use format 'scenes_X_Y' or 'X-Y'",
            ))

    return issues


def validate_locations(config: ProductionConfig) -> List[ValidationIssue]:
    """
    Validate location configurations.

    Args:
        config: Production configuration

    Returns:
        List of validation issues
    """
    issues = []

    # Check for locations
    if not config.locations:
        issues.append(ValidationIssue(
            path="locations",
            severity=ValidationSeverity.INFO.value,
            message="No locations defined",
            suggestion="Add location configurations for location-based shots",
        ))
        return issues

    for name, loc in config.locations.items():
        issues.extend(_validate_location(name, loc, config))

    return issues


def _validate_location(name: str, loc: LocationConfig, config: ProductionConfig) -> List[ValidationIssue]:
    """Validate single location."""
    issues = []

    # Check name matches key
    if loc.name and loc.name != name:
        issues.append(ValidationIssue(
            path=f"locations.{name}.name",
            severity=ValidationSeverity.WARNING.value,
            message=f"Location name '{loc.name}' does not match key '{name}'",
            suggestion="Ensure location name matches the dictionary key",
        ))

    # Check preset or HDRI
    if not loc.preset and not loc.hdri:
        issues.append(ValidationIssue(
            path=f"locations.{name}",
            severity=ValidationSeverity.WARNING.value,
            message=f"Location '{name}' has no preset or HDRI specified",
            suggestion="Specify either a set builder preset or HDRI file",
        ))

    # Check HDRI path if specified
    if loc.hdri and not loc.hdri.startswith("preset:"):
        full_path = _resolve_path(loc.hdri, config.base_path)
        if not os.path.exists(full_path):
            issues.append(ValidationIssue(
                path=f"locations.{name}.hdri",
                severity=ValidationSeverity.ERROR.value,
                message=f"HDRI file not found: {loc.hdri}",
                suggestion="Verify the HDRI file path exists",
            ))

    return issues


def validate_shots(config: ProductionConfig) -> List[ValidationIssue]:
    """
    Validate shot configurations.

    Args:
        config: Production configuration

    Returns:
        List of validation issues
    """
    issues = []

    # Check for shots
    if not config.shots:
        issues.append(ValidationIssue(
            path="shots",
            severity=ValidationSeverity.ERROR.value,
            message="No shots defined",
            suggestion="Add at least one shot configuration",
        ))
        return issues

    # Track scene numbers
    scenes_used = set()

    for i, shot in enumerate(config.shots):
        shot_issues = _validate_shot(i, shot, config)
        issues.extend(shot_issues)

        if shot.scene > 0:
            scenes_used.add(shot.scene)

    # Check for gaps in scene numbers
    if scenes_used:
        max_scene = max(scenes_used)
        for s in range(1, max_scene + 1):
            if s not in scenes_used:
                issues.append(ValidationIssue(
                    path="shots",
                    severity=ValidationSeverity.INFO.value,
                    message=f"Scene {s} has no shots",
                    suggestion="Verify scene numbering is intentional",
                ))

    return issues


def _validate_shot(index: int, shot: ShotConfig, config: ProductionConfig) -> List[ValidationIssue]:
    """Validate single shot."""
    issues = []
    path = f"shots[{index}]"

    # Check name
    if not shot.name:
        issues.append(ValidationIssue(
            path=f"{path}.name",
            severity=ValidationSeverity.WARNING.value,
            message=f"Shot {index} has no name",
            suggestion="Add a descriptive shot name",
        ))

    # Check template
    if not shot.template:
        issues.append(ValidationIssue(
            path=f"{path}.template",
            severity=ValidationSeverity.WARNING.value,
            message=f"Shot '{shot.name or index}' has no template",
            suggestion="Specify a shot template for consistent rendering",
        ))

    # Check character reference
    if shot.character:
        if shot.character not in config.characters:
            issues.append(ValidationIssue(
                path=f"{path}.character",
                severity=ValidationSeverity.ERROR.value,
                message=f"Shot references unknown character: {shot.character}",
                suggestion=f"Add character '{shot.character}' to characters section",
            ))

    # Check location reference
    if shot.location:
        if shot.location not in config.locations:
            issues.append(ValidationIssue(
                path=f"{path}.location",
                severity=ValidationSeverity.ERROR.value,
                message=f"Shot references unknown location: {shot.location}",
                suggestion=f"Add location '{shot.location}' to locations section",
            ))

    # Check frame range
    if shot.frame_range[0] > shot.frame_range[1]:
        issues.append(ValidationIssue(
            path=f"{path}.frame_range",
            severity=ValidationSeverity.ERROR.value,
            message=f"Invalid frame range: {shot.frame_range}",
            suggestion="Ensure start frame is before end frame",
        ))

    # Check duration matches frame range
    expected_duration = shot.frame_range[1] - shot.frame_range[0] + 1
    if shot.duration != expected_duration and shot.duration != 120:  # 120 is default
        issues.append(ValidationIssue(
            path=f"{path}.duration",
            severity=ValidationSeverity.WARNING.value,
            message=f"Duration ({shot.duration}) doesn't match frame range ({expected_duration})",
            suggestion="Update duration to match frame range",
        ))

    return issues


def validate_dependencies(config: ProductionConfig) -> List[ValidationIssue]:
    """
    Validate all file references exist.

    Args:
        config: Production configuration

    Returns:
        List of validation issues
    """
    issues = []

    # Check script file
    if config.script_path:
        full_path = _resolve_path(config.script_path, config.base_path)
        if not os.path.exists(full_path):
            issues.append(ValidationIssue(
                path="script_path",
                severity=ValidationSeverity.ERROR.value,
                message=f"Script file not found: {config.script_path}",
                suggestion="Verify the script file path exists",
            ))

    # Check shot list file
    if config.shot_list_path:
        full_path = _resolve_path(config.shot_list_path, config.base_path)
        if not os.path.exists(full_path):
            issues.append(ValidationIssue(
                path="shot_list_path",
                severity=ValidationSeverity.ERROR.value,
                message=f"Shot list file not found: {config.shot_list_path}",
                suggestion="Verify the shot list file path exists",
            ))

    # Check output directories (create if needed)
    for i, output in enumerate(config.outputs):
        if output.output_path:
            full_path = _resolve_path(output.output_path, config.base_path)
            if not os.path.exists(full_path):
                issues.append(ValidationIssue(
                    path=f"outputs[{i}].output_path",
                    severity=ValidationSeverity.INFO.value,
                    message=f"Output directory does not exist: {output.output_path}",
                    suggestion="Directory will be created during execution",
                ))

    return issues


def validate_timeline(config: ProductionConfig) -> List[ValidationIssue]:
    """
    Validate timeline consistency.

    Args:
        config: Production configuration

    Returns:
        List of validation issues
    """
    issues = []

    if not config.shots:
        return issues

    # Sort shots by frame range
    sorted_shots = sorted(
        enumerate(config.shots),
        key=lambda x: x[1].frame_range[0]
    )

    # Check for frame overlaps
    prev_end = 0
    for i, shot in sorted_shots:
        start, end = shot.frame_range

        if start < prev_end:
            issues.append(ValidationIssue(
                path=f"shots[{i}].frame_range",
                severity=ValidationSeverity.WARNING.value,
                message=f"Shot '{shot.name or i}' overlaps with previous shot",
                suggestion="Adjust frame ranges to avoid overlaps",
            ))

        prev_end = max(prev_end, end)

    # Check for frame gaps
    prev_end = 0
    for i, shot in sorted_shots:
        start, end = shot.frame_range

        if start > prev_end + 1 and prev_end > 0:
            issues.append(ValidationIssue(
                path=f"shots[{i}].frame_range",
                severity=ValidationSeverity.INFO.value,
                message=f"Frame gap between shot {prev_end} and {start}",
                suggestion="Verify gap is intentional",
            ))

        prev_end = max(prev_end, end)

    return issues


def validate_outputs(config: ProductionConfig) -> List[ValidationIssue]:
    """
    Validate output configurations.

    Args:
        config: Production configuration

    Returns:
        List of validation issues
    """
    issues = []

    if not config.outputs:
        issues.append(ValidationIssue(
            path="outputs",
            severity=ValidationSeverity.WARNING.value,
            message="No output formats defined",
            suggestion="Add at least one output format",
        ))
        return issues

    for i, output in enumerate(config.outputs):
        issues.extend(_validate_output(i, output))

    return issues


def _validate_output(index: int, output: OutputFormat) -> List[ValidationIssue]:
    """Validate single output format."""
    issues = []
    path = f"outputs[{index}]"

    # Check format
    if not output.format:
        issues.append(ValidationIssue(
            path=f"{path}.format",
            severity=ValidationSeverity.ERROR.value,
            message="Output format not specified",
            suggestion="Specify output format (e.g., cinema_4k, streaming_1080p)",
        ))

    # Check resolution
    if output.resolution[0] <= 0 or output.resolution[1] <= 0:
        issues.append(ValidationIssue(
            path=f"{path}.resolution",
            severity=ValidationSeverity.ERROR.value,
            message=f"Invalid resolution: {output.resolution}",
            suggestion="Set valid width and height",
        ))

    # Check frame rate
    if output.frame_rate <= 0:
        issues.append(ValidationIssue(
            path=f"{path}.frame_rate",
            severity=ValidationSeverity.ERROR.value,
            message=f"Invalid frame rate: {output.frame_rate}",
            suggestion="Set valid frame rate (e.g., 24, 30, 60)",
        ))

    # Check retro config if enabled
    if output.retro_config and output.retro_config.enabled:
        if output.retro_config.pixel_size < 1:
            issues.append(ValidationIssue(
                path=f"{path}.retro_config.pixel_size",
                severity=ValidationSeverity.ERROR.value,
                message=f"Invalid pixel size: {output.retro_config.pixel_size}",
                suggestion="Set pixel size >= 1",
            ))

    return issues


def _resolve_path(path: str, base_path: str) -> str:
    """Resolve path relative to base path."""
    if os.path.isabs(path):
        return path
    if base_path:
        return os.path.normpath(os.path.join(base_path, path))
    return os.path.normpath(path)


def _is_valid_scene_range(range_key: str) -> bool:
    """Check if scene range format is valid."""
    # Format: "scenes_X_Y" or "X-Y"
    if range_key.startswith("scenes_"):
        parts = range_key.replace("scenes_", "").split("_")
        if len(parts) == 2:
            try:
                int(parts[0])
                int(parts[1])
                return True
            except ValueError:
                return False
    elif "-" in range_key:
        parts = range_key.split("-")
        if len(parts) == 2:
            try:
                int(parts[0])
                int(parts[1])
                return True
            except ValueError:
                return False
    return False


def validate_for_execution(config: ProductionConfig) -> ValidationResult:
    """
    Validate production is ready for execution.

    This is a stricter validation that ensures the production
    can actually be executed without errors.

    Args:
        config: Production configuration

    Returns:
        ValidationResult with any blocking issues
    """
    result = validate_production(config)

    # Additional execution-specific checks

    # Must have at least one output
    if not config.outputs:
        result.add_error(
            "outputs",
            "Cannot execute production without output formats",
            "Add at least one output format"
        )

    # Must have at least one shot
    if not config.shots:
        result.add_error(
            "shots",
            "Cannot execute production without shots",
            "Add at least one shot configuration"
        )

    # All referenced characters must exist
    for i, shot in enumerate(config.shots):
        if shot.character and shot.character not in config.characters:
            result.add_error(
                f"shots[{i}].character",
                f"Shot references missing character: {shot.character}",
                f"Add character '{shot.character}' configuration"
            )

    # All referenced locations must exist
    for i, shot in enumerate(config.shots):
        if shot.location and shot.location not in config.locations:
            result.add_error(
                f"shots[{i}].location",
                f"Shot references missing location: {shot.location}",
                f"Add location '{shot.location}' configuration"
            )

    return result
