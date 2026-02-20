"""
Config Validation

Validation functions for master production configurations.

This module provides comprehensive validation for master production
configurations, including file reference checking, model validation,
preset validation, and output format validation.

Requirements:
- REQ-CONFIG-01 through REQ-CONFIG-06: Configuration validation

Part of Phase 14.2: Master Production Config
"""

from __future__ import annotations
import os
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass

from .config_schema import (
    MasterProductionConfig,
    CharacterDef,
    LocationDef,
    ShotDef,
    OutputDef,
    RetroOutputConfig,
)
from .production_types import (
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
)
from .template_expansion import (
    SHOT_TEMPLATES,
    STYLE_PRESETS,
)


def validate_master_config(config: MasterProductionConfig) -> ValidationResult:
    """
    Complete validation of production config.

    Runs all validation checks and aggregates results.

    Args:
        config: Master production configuration

    Returns:
        ValidationResult with all issues
    """
    result = ValidationResult(valid=True)

    # Run all validation checks
    issues = []
    issues.extend(validate_meta(config))
    issues.extend(validate_source(config))
    issues.extend(validate_character_defs(config))
    issues.extend(validate_location_defs(config))
    issues.extend(validate_shot_defs(config))
    issues.extend(check_file_references(config))
    issues.extend(validate_output_defs(config))

    # Add all issues
    for issue in issues:
        if issue.severity == ValidationSeverity.ERROR.value:
            result.add_error(issue.path, issue.message, issue.suggestion)
        elif issue.severity == ValidationSeverity.WARNING.value:
            result.add_warning(issue.path, issue.message, issue.suggestion)
        else:
            result.issues.append(issue)

    return result


def validate_meta(config: MasterProductionConfig) -> List[ValidationIssue]:
    """
    Validate production metadata.

    Args:
        config: Master production configuration

    Returns:
        List of validation issues
    """
    issues = []

    if not config.meta.title:
        issues.append(ValidationIssue(
            path="meta.title",
            severity=ValidationSeverity.WARNING.value,
            message="Production title is empty",
            suggestion="Set a descriptive title for the production",
        ))

    if not config.meta.author:
        issues.append(ValidationIssue(
            path="meta.author",
            severity=ValidationSeverity.INFO.value,
            message="Author not specified",
            suggestion="Add author information for attribution",
        ))

    if not config.meta.description:
        issues.append(ValidationIssue(
            path="meta.description",
            severity=ValidationSeverity.INFO.value,
            message="No description provided",
            suggestion="Add a description to document the production",
        ))

    return issues


def validate_source(config: MasterProductionConfig) -> List[ValidationIssue]:
    """
    Validate source configuration.

    Args:
        config: Master production configuration

    Returns:
        List of validation issues
    """
    issues = []

    # Check script file
    if config.source.script:
        full_path = _resolve_path(config.source.script, config.base_path)
        if not os.path.exists(full_path):
            issues.append(ValidationIssue(
                path="source.script",
                severity=ValidationSeverity.WARNING.value,
                message=f"Script file not found: {config.source.script}",
                suggestion="Verify the script file path exists",
            ))

    # Check style preset
    if config.source.style_preset:
        if config.source.style_preset not in STYLE_PRESETS:
            issues.append(ValidationIssue(
                path="source.style_preset",
                severity=ValidationSeverity.WARNING.value,
                message=f"Unknown style preset: {config.source.style_preset}",
                suggestion=f"Available presets: {', '.join(STYLE_PRESETS.keys())}",
            ))

    # Check reference images
    for i, ref_img in enumerate(config.source.reference_images):
        full_path = _resolve_path(ref_img, config.base_path)
        if not os.path.exists(full_path):
            issues.append(ValidationIssue(
                path=f"source.reference_images[{i}]",
                severity=ValidationSeverity.WARNING.value,
                message=f"Reference image not found: {ref_img}",
                suggestion="Verify the reference image path exists",
            ))

    return issues


def validate_character_defs(config: MasterProductionConfig) -> List[ValidationIssue]:
    """
    Validate character definitions.

    Args:
        config: Master production configuration

    Returns:
        List of validation issues
    """
    issues = []

    if not config.characters:
        issues.append(ValidationIssue(
            path="characters",
            severity=ValidationSeverity.INFO.value,
            message="No characters defined",
            suggestion="Add character configurations for character-based shots",
        ))
        return issues

    for name, char in config.characters.items():
        issues.extend(_validate_character_def(name, char, config))

    return issues


def _validate_character_def(
    name: str,
    char: CharacterDef,
    config: MasterProductionConfig
) -> List[ValidationIssue]:
    """Validate single character definition."""
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
    else:
        issues.append(ValidationIssue(
            path=f"characters.{name}.model",
            severity=ValidationSeverity.WARNING.value,
            message=f"Character '{name}' has no model file specified",
            suggestion="Add a model file path for the character",
        ))

    # Check wardrobe assignments
    for range_key, costume in char.wardrobe.items():
        if range_key != "default" and not _is_valid_scene_range(range_key):
            issues.append(ValidationIssue(
                path=f"characters.{name}.wardrobe.{range_key}",
                severity=ValidationSeverity.WARNING.value,
                message=f"Invalid scene range format: {range_key}",
                suggestion="Use format 'scenes_X_Y' or 'X-Y'",
            ))

    return issues


def validate_location_defs(config: MasterProductionConfig) -> List[ValidationIssue]:
    """
    Validate location definitions.

    Args:
        config: Master production configuration

    Returns:
        List of validation issues
    """
    issues = []

    if not config.locations:
        issues.append(ValidationIssue(
            path="locations",
            severity=ValidationSeverity.INFO.value,
            message="No locations defined",
            suggestion="Add location configurations for location-based shots",
        ))
        return issues

    for name, loc in config.locations.items():
        issues.extend(_validate_location_def(name, loc, config))

    return issues


def _validate_location_def(
    name: str,
    loc: LocationDef,
    config: MasterProductionConfig
) -> List[ValidationIssue]:
    """Validate single location definition."""
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
    if not loc.preset and not loc.hdri and not loc.custom_setup:
        issues.append(ValidationIssue(
            path=f"locations.{name}",
            severity=ValidationSeverity.WARNING.value,
            message=f"Location '{name}' has no preset, HDRI, or custom setup specified",
            suggestion="Specify a set preset, HDRI file, or custom .blend file",
        ))

    # Check HDRI file if specified
    if loc.hdri and not loc.hdri.startswith("preset:"):
        full_path = _resolve_path(loc.hdri, config.base_path)
        if not os.path.exists(full_path):
            issues.append(ValidationIssue(
                path=f"locations.{name}.hdri",
                severity=ValidationSeverity.ERROR.value,
                message=f"HDRI file not found: {loc.hdri}",
                suggestion="Verify the HDRI file path exists",
            ))

    # Check custom setup file
    if loc.custom_setup:
        full_path = _resolve_path(loc.custom_setup, config.base_path)
        if not os.path.exists(full_path):
            issues.append(ValidationIssue(
                path=f"locations.{name}.custom_setup",
                severity=ValidationSeverity.ERROR.value,
                message=f"Custom setup file not found: {loc.custom_setup}",
                suggestion="Verify the custom .blend file path exists",
            ))

    return issues


def validate_shot_defs(config: MasterProductionConfig) -> List[ValidationIssue]:
    """
    Validate shot definitions.

    Args:
        config: Master production configuration

    Returns:
        List of validation issues
    """
    issues = []

    if not config.shots:
        issues.append(ValidationIssue(
            path="shots",
            severity=ValidationSeverity.ERROR.value,
            message="No shots defined",
            suggestion="Add at least one shot configuration",
        ))
        return issues

    # Track scenes and characters used
    scenes_used: Set[int] = set()

    for i, shot in enumerate(config.shots):
        shot_issues = _validate_shot_def(i, shot, config)
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


def _validate_shot_def(
    index: int,
    shot: ShotDef,
    config: MasterProductionConfig
) -> List[ValidationIssue]:
    """Validate single shot definition."""
    issues = []
    path = f"shots[{index}]"

    # Check name
    if not shot.name:
        issues.append(ValidationIssue(
            path=f"{path}.name",
            severity=ValidationSeverity.INFO.value,
            message=f"Shot {index} has no name (will be auto-generated)",
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
    elif shot.template not in SHOT_TEMPLATES:
        issues.append(ValidationIssue(
            path=f"{path}.template",
            severity=ValidationSeverity.WARNING.value,
            message=f"Unknown shot template: {shot.template}",
            suggestion=f"Available templates: {', '.join(list(SHOT_TEMPLATES.keys())[:5])}...",
        ))

    # Check character references
    if shot.character:
        if shot.character not in config.characters:
            issues.append(ValidationIssue(
                path=f"{path}.character",
                severity=ValidationSeverity.ERROR.value,
                message=f"Shot references unknown character: {shot.character}",
                suggestion=f"Add character '{shot.character}' to characters section",
            ))

    if shot.character2:
        if shot.character2 not in config.characters:
            issues.append(ValidationIssue(
                path=f"{path}.character2",
                severity=ValidationSeverity.ERROR.value,
                message=f"Shot references unknown character: {shot.character2}",
                suggestion=f"Add character '{shot.character2}' to characters section",
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
    if shot.frame_range != (0, 0):
        if shot.frame_range[0] > shot.frame_range[1]:
            issues.append(ValidationIssue(
                path=f"{path}.frame_range",
                severity=ValidationSeverity.ERROR.value,
                message=f"Invalid frame range: {shot.frame_range}",
                suggestion="Ensure start frame is before end frame",
            ))

    # Check scene number
    if shot.scene == 0:
        issues.append(ValidationIssue(
            path=f"{path}.scene",
            severity=ValidationSeverity.INFO.value,
            message=f"Shot '{shot.name or index}' has no scene number",
            suggestion="Assign a scene number for organization",
        ))

    return issues


def check_file_references(config: MasterProductionConfig) -> List[ValidationIssue]:
    """
    Check all file paths exist.

    Args:
        config: Master production configuration

    Returns:
        List of validation issues
    """
    issues = []

    # Check script
    if config.source.script:
        full_path = _resolve_path(config.source.script, config.base_path)
        if not os.path.exists(full_path):
            issues.append(ValidationIssue(
                path="source.script",
                severity=ValidationSeverity.WARNING.value,
                message=f"Script file not found: {config.source.script}",
                suggestion="Verify the script file path",
            ))

    # Check character models
    for name, char in config.characters.items():
        if char.model:
            full_path = _resolve_path(char.model, config.base_path)
            if not os.path.exists(full_path):
                issues.append(ValidationIssue(
                    path=f"characters.{name}.model",
                    severity=ValidationSeverity.ERROR.value,
                    message=f"Character model not found: {char.model}",
                    suggestion="Verify the model file exists",
                ))

    # Check location HDRIs and custom setups
    for name, loc in config.locations.items():
        if loc.hdri and not loc.hdri.startswith("preset:"):
            full_path = _resolve_path(loc.hdri, config.base_path)
            if not os.path.exists(full_path):
                issues.append(ValidationIssue(
                    path=f"locations.{name}.hdri",
                    severity=ValidationSeverity.ERROR.value,
                    message=f"HDRI file not found: {loc.hdri}",
                    suggestion="Verify the HDRI file exists",
                ))

        if loc.custom_setup:
            full_path = _resolve_path(loc.custom_setup, config.base_path)
            if not os.path.exists(full_path):
                issues.append(ValidationIssue(
                    path=f"locations.{name}.custom_setup",
                    severity=ValidationSeverity.ERROR.value,
                    message=f"Custom setup file not found: {loc.custom_setup}",
                    suggestion="Verify the custom .blend file exists",
                ))

    # Check output directories (info only)
    for i, output in enumerate(config.outputs):
        if output.path:
            full_path = _resolve_path(output.path, config.base_path)
            if not os.path.exists(full_path):
                issues.append(ValidationIssue(
                    path=f"outputs[{i}].path",
                    severity=ValidationSeverity.INFO.value,
                    message=f"Output directory does not exist: {output.path}",
                    suggestion="Directory will be created during execution",
                ))

    return issues


def check_character_models(config: MasterProductionConfig) -> List[ValidationIssue]:
    """
    Validate character model references.

    Args:
        config: Master production configuration

    Returns:
        List of validation issues
    """
    issues = []

    for name, char in config.characters.items():
        if not char.model:
            issues.append(ValidationIssue(
                path=f"characters.{name}.model",
                severity=ValidationSeverity.WARNING.value,
                message=f"Character '{name}' has no model file",
                suggestion="Add a model file for this character",
            ))
        else:
            full_path = _resolve_path(char.model, config.base_path)
            if not os.path.exists(full_path):
                issues.append(ValidationIssue(
                    path=f"characters.{name}.model",
                    severity=ValidationSeverity.ERROR.value,
                    message=f"Model file not found: {char.model}",
                    suggestion="Verify the model file path",
                ))

    return issues


def check_location_presets(config: MasterProductionConfig) -> List[ValidationIssue]:
    """
    Validate location preset references.

    Args:
        config: Master production configuration

    Returns:
        List of validation issues
    """
    issues = []

    # Known set builder presets (partial list)
    known_presets = {
        "modern", "victorian", "scifi", "cyberpunk", "scandinavian",
        "industrial", "office", "apartment", "warehouse", "street",
        "forest", "beach", "mountain", "desert", "urban_rooftop",
        "corporate_office", "modern_apartment", "abandoned_warehouse",
    }

    for name, loc in config.locations.items():
        if loc.preset and loc.preset not in known_presets:
            issues.append(ValidationIssue(
                path=f"locations.{name}.preset",
                severity=ValidationSeverity.INFO.value,
                message=f"Location uses custom preset: {loc.preset}",
                suggestion="Verify the preset exists in set builder",
            ))

    return issues


def check_shot_templates(config: MasterProductionConfig) -> List[ValidationIssue]:
    """
    Validate shot template references.

    Args:
        config: Master production configuration

    Returns:
        List of validation issues
    """
    issues = []

    for i, shot in enumerate(config.shots):
        if shot.template and shot.template not in SHOT_TEMPLATES:
            issues.append(ValidationIssue(
                path=f"shots[{i}].template",
                severity=ValidationSeverity.WARNING.value,
                message=f"Unknown shot template: {shot.template}",
                suggestion=f"Available templates: {', '.join(list(SHOT_TEMPLATES.keys())[:5])}...",
            ))

    return issues


def validate_output_defs(config: MasterProductionConfig) -> List[ValidationIssue]:
    """
    Validate output format specifications.

    Args:
        config: Master production configuration

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
        issues.extend(_validate_output_def(i, output))

    return issues


def _validate_output_def(index: int, output: OutputDef) -> List[ValidationIssue]:
    """Validate single output definition."""
    issues = []
    path = f"outputs[{index}]"

    # Check name
    if not output.name:
        issues.append(ValidationIssue(
            path=f"{path}.name",
            severity=ValidationSeverity.WARNING.value,
            message=f"Output {index} has no name",
            suggestion="Add a descriptive name for the output format",
        ))

    # Check format
    if not output.format:
        issues.append(ValidationIssue(
            path=f"{path}.format",
            severity=ValidationSeverity.ERROR.value,
            message="Output format not specified",
            suggestion="Specify output format (e.g., prores_4444, h264, png_sequence)",
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

    # Check retro config
    if output.retro and output.retro.enabled:
        issues.extend(_validate_retro_config(path, output.retro))

    return issues


def _validate_retro_config(path: str, retro: RetroOutputConfig) -> List[ValidationIssue]:
    """Validate retro output configuration."""
    issues = []

    # Known palettes
    known_palettes = {
        "snes", "nes", "gameboy", "pico8", "cga", "ega", "mac_plus",
        "genesis", "spectrum", "c64", "amstrad", "msx",
    }

    if retro.palette and retro.palette not in known_palettes:
        issues.append(ValidationIssue(
            path=f"{path}.retro.palette",
            severity=ValidationSeverity.WARNING.value,
            message=f"Unknown palette: {retro.palette}",
            suggestion=f"Known palettes: {', '.join(sorted(known_palettes))}",
        ))

    # Known dither modes
    known_dither = {"none", "ordered", "error_diffusion", "atkinson", "floyd_steinberg"}

    if retro.dither and retro.dither not in known_dither:
        issues.append(ValidationIssue(
            path=f"{path}.retro.dither",
            severity=ValidationSeverity.WARNING.value,
            message=f"Unknown dither mode: {retro.dither}",
            suggestion=f"Known modes: {', '.join(sorted(known_dither))}",
        ))

    # Check pixel size
    if retro.pixel_size < 1:
        issues.append(ValidationIssue(
            path=f"{path}.retro.pixel_size",
            severity=ValidationSeverity.ERROR.value,
            message=f"Invalid pixel size: {retro.pixel_size}",
            suggestion="Set pixel size >= 1",
        ))

    # Check target resolution
    if retro.target_resolution[0] <= 0 or retro.target_resolution[1] <= 0:
        issues.append(ValidationIssue(
            path=f"{path}.retro.target_resolution",
            severity=ValidationSeverity.ERROR.value,
            message=f"Invalid target resolution: {retro.target_resolution}",
            suggestion="Set valid width and height",
        ))

    return issues


def validate_for_execution_strict(config: MasterProductionConfig) -> ValidationResult:
    """
    Strict validation for execution readiness.

    This validation ensures the production can actually be executed
    without blocking errors.

    Args:
        config: Master production configuration

    Returns:
        ValidationResult with any blocking issues
    """
    result = validate_master_config(config)

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

    # All referenced characters must exist with models
    referenced_chars = set()
    for shot in config.shots:
        if shot.character:
            referenced_chars.add(shot.character)
        if shot.character2:
            referenced_chars.add(shot.character2)

    for char_name in referenced_chars:
        if char_name not in config.characters:
            result.add_error(
                "shots",
                f"Referenced character '{char_name}' not defined",
                f"Add character '{char_name}' to characters section"
            )
        elif not config.characters[char_name].model:
            result.add_error(
                f"characters.{char_name}.model",
                f"Character '{char_name}' has no model file",
                "Add a model file for the character"
            )

    # All referenced locations must have setup
    referenced_locs = set()
    for shot in config.shots:
        if shot.location:
            referenced_locs.add(shot.location)

    for loc_name in referenced_locs:
        if loc_name not in config.locations:
            result.add_error(
                "shots",
                f"Referenced location '{loc_name}' not defined",
                f"Add location '{loc_name}' to locations section"
            )
        else:
            loc = config.locations[loc_name]
            if not loc.preset and not loc.hdri and not loc.custom_setup:
                result.add_warning(
                    f"locations.{loc_name}",
                    f"Location '{loc_name}' has no setup configuration",
                    "Specify preset, HDRI, or custom setup"
                )

    return result


def _resolve_path(path: str, base_path: str) -> str:
    """Resolve path relative to base path."""
    if os.path.isabs(path):
        return path
    if base_path:
        return os.path.normpath(os.path.join(base_path, path))
    return os.path.normpath(path)


def _is_valid_scene_range(range_key: str) -> bool:
    """Check if scene range format is valid."""
    if range_key == "default":
        return True
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
