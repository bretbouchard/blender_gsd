"""
MSG 1998 - Modeling Pipeline

Universal Stage Order pipeline for location building.
"""

from typing import Any, Dict, List, Optional

from .types import (
    LocationBuildState,
    ModelingStage,
    PeriodViolation,
    PeriodViolationSeverity
)


class StageValidator:
    """Validates completion of each modeling stage."""

    @staticmethod
    def validate_normalize(state: LocationBuildState) -> List[str]:
        """Validate Stage 0: Normalize."""
        errors = []

        if not state.geometry_stats.get("scale_normalized", False):
            errors.append("Geometry not normalized to real-world scale (meters)")

        if not state.geometry_stats.get("origin_at_ground", False):
            errors.append("Origin not at ground level")

        return errors

    @staticmethod
    def validate_primary(state: LocationBuildState) -> List[str]:
        """Validate Stage 1: Primary geometry."""
        errors = []

        if not state.geometry_stats.get("has_base_geometry", False):
            errors.append("Missing base building geometry")

        if not state.geometry_stats.get("watertight", True):
            errors.append("Primary geometry has holes (not watertight)")

        return errors

    @staticmethod
    def validate_secondary(state: LocationBuildState) -> List[str]:
        """Validate Stage 2: Secondary details."""
        errors = []

        if not state.geometry_stats.get("has_windows", False):
            errors.append("No windows added (expected for building)")

        if not state.geometry_stats.get("has_doors", False):
            errors.append("No doors added")

        return errors

    @staticmethod
    def validate_detail(state: LocationBuildState) -> List[str]:
        """Validate Stage 3: Detail."""
        errors = []

        if not state.geometry_stats.get("has_materials", False):
            errors.append("No materials assigned")

        return errors

    @staticmethod
    def validate_output_prep(state: LocationBuildState) -> List[str]:
        """Validate Stage 4: OutputPrep."""
        errors = []

        if not state.geometry_stats.get("render_layers_setup", False):
            errors.append("Render layers not configured")

        if not state.geometry_stats.get("passes_enabled", False):
            errors.append("Render passes not enabled")

        return errors


def advance_stage(
    state: LocationBuildState,
    next_stage: ModelingStage,
    force: bool = False
) -> LocationBuildState:
    """
    Advance to next modeling stage with validation.

    Universal Stage Order:
    0. NORMALIZE - Scale to real-world units (meters)
    1. PRIMARY - Base geometry (walls, roof)
    2. SECONDARY - Windows, doors, architectural details
    3. DETAIL - Textures, wear, signage
    4. OUTPUT_PREP - Render layer setup

    Args:
        state: Current build state
        next_stage: Target stage
        force: Skip validation if True

    Returns:
        Updated build state
    """
    # Check if advancing in order
    if next_stage.value > state.current_stage.value + 1 and not force:
        raise ValueError(
            f"Cannot skip stages. Current: {state.current_stage.name}, "
            f"Requested: {next_stage.name}. "
            f"Use force=True to override."
        )

    # Validate current stage completion
    if not force:
        validator = StageValidator()
        validation_methods = {
            ModelingStage.NORMALIZE: validator.validate_normalize,
            ModelingStage.PRIMARY: validator.validate_primary,
            ModelingStage.SECONDARY: validator.validate_secondary,
            ModelingStage.DETAIL: validator.validate_detail,
            ModelingStage.OUTPUT_PREP: validator.validate_output_prep,
        }

        if state.current_stage in validation_methods:
            errors = validation_methods[state.current_stage](state)
            if errors:
                raise ValueError(
                    f"Cannot advance from {state.current_stage.name}. "
                    f"Errors: {', '.join(errors)}"
                )

    # Record completed task
    state.completed_tasks.append(f"Completed {state.current_stage.name}")

    # Advance stage
    state.current_stage = next_stage

    return state


def create_build_state(location_id: str) -> LocationBuildState:
    """
    Create initial build state for a location.

    Args:
        location_id: Location identifier

    Returns:
        New LocationBuildState at NORMALIZE stage
    """
    return LocationBuildState(
        location_id=location_id,
        current_stage=ModelingStage.NORMALIZE,
        geometry_stats={
            "scale_normalized": False,
            "origin_at_ground": False,
            "has_base_geometry": False,
            "watertight": True,
            "has_windows": False,
            "has_doors": False,
            "has_materials": False,
            "render_layers_setup": False,
            "passes_enabled": False,
        },
        period_issues=[],
        completed_tasks=[],
    )


def update_geometry_stats(
    state: LocationBuildState,
    stats: Dict[str, Any]
) -> LocationBuildState:
    """
    Update geometry statistics for the build state.

    Args:
        state: Current build state
        stats: New statistics to merge

    Returns:
        Updated build state
    """
    state.geometry_stats.update(stats)
    return state


def add_period_issue(
    state: LocationBuildState,
    issue: PeriodViolation
) -> LocationBuildState:
    """
    Add a period accuracy issue to the build state.

    Args:
        state: Current build state
        issue: Period violation found

    Returns:
        Updated build state
    """
    state.period_issues.append(issue)
    return state


def get_stage_progress(state: LocationBuildState) -> Dict[str, Any]:
    """
    Get progress information for current build.

    Args:
        state: Current build state

    Returns:
        Dict with progress information
    """
    total_stages = len(ModelingStage)
    current_stage_value = state.current_stage.value
    progress_percent = (current_stage_value / (total_stages - 1)) * 100

    return {
        "location_id": state.location_id,
        "current_stage": state.current_stage.name,
        "stage_number": current_stage_value,
        "total_stages": total_stages,
        "progress_percent": round(progress_percent, 1),
        "completed_tasks": len(state.completed_tasks),
        "period_issues": len(state.period_issues),
        "critical_period_issues": sum(
            1 for issue in state.period_issues
            if issue.severity == PeriodViolationSeverity.ERROR
        ),
        "ready_for_next_stage": current_stage_value < total_stages - 1,
        "ready_for_render": state.current_stage == ModelingStage.OUTPUT_PREP,
    }


def validate_stage_completion(state: LocationBuildState) -> Dict[str, Any]:
    """
    Validate that current stage is complete enough to advance.

    This implements the Council recommendation for stage gates.

    Args:
        state: Current build state

    Returns:
        Validation result with can_advance, errors, warnings
    """
    validator = StageValidator()
    validation_methods = {
        ModelingStage.NORMALIZE: validator.validate_normalize,
        ModelingStage.PRIMARY: validator.validate_primary,
        ModelingStage.SECONDARY: validator.validate_secondary,
        ModelingStage.DETAIL: validator.validate_detail,
        ModelingStage.OUTPUT_PREP: validator.validate_output_prep,
    }

    errors = []
    warnings = []

    # Run stage validation
    if state.current_stage in validation_methods:
        stage_errors = validation_methods[state.current_stage](state)
        errors.extend(stage_errors)

    # Check for blocking period issues
    critical_period = sum(
        1 for issue in state.period_issues
        if issue.severity == PeriodViolationSeverity.ERROR
    )
    if critical_period > 0:
        warnings.append(f"{critical_period} critical period accuracy issues found")

    return {
        "can_advance": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stage": state.current_stage.name,
    }


# Stage completion helpers
def mark_scale_normalized(state: LocationBuildState) -> LocationBuildState:
    """Mark geometry as normalized to real-world scale."""
    return update_geometry_stats(state, {"scale_normalized": True, "origin_at_ground": True})


def mark_base_geometry_complete(state: LocationBuildState, watertight: bool = True) -> LocationBuildState:
    """Mark primary geometry as complete."""
    return update_geometry_stats(state, {
        "has_base_geometry": True,
        "watertight": watertight
    })


def mark_secondary_complete(state: LocationBuildState, has_windows: bool, has_doors: bool) -> LocationBuildState:
    """Mark secondary details as complete."""
    return update_geometry_stats(state, {
        "has_windows": has_windows,
        "has_doors": has_doors
    })


def mark_detail_complete(state: LocationBuildState) -> LocationBuildState:
    """Mark detail stage as complete."""
    return update_geometry_stats(state, {"has_materials": True})


def mark_output_prep_complete(state: LocationBuildState) -> LocationBuildState:
    """Mark output prep as complete."""
    return update_geometry_stats(state, {
        "render_layers_setup": True,
        "passes_enabled": True
    })
