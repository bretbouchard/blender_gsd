"""
Production Orchestrator Package

Master orchestrator for one-command production execution.

This package provides the production management system that ties together
all other systems (cinematic, retro, character, etc.) for automated
production workflows.

Requirements:
- REQ-ORCH-01: Load complete production from YAML
- REQ-ORCH-02: Validate production before execution
- REQ-ORCH-03: Execute all phases in order
- REQ-ORCH-04: Progress tracking and resume
- REQ-ORCH-05: Parallel execution where possible
- REQ-ORCH-06: Error handling and rollback

Usage:
    from lib.production import (
        ProductionConfig,
        load_production,
        execute_production,
        validate_production,
    )

    # Load and execute
    config = load_production("my_film/production.yaml")
    result = execute_production(config)

Part of Phase 14.1: Production Orchestrator
"""

# Core types
from .production_types import (
    # Enums
    ExecutionPhase,
    ExecutionStatus,
    ValidationSeverity,
    EXECUTION_PHASES,

    # Metadata
    ProductionMeta,

    # Configuration
    CharacterConfig,
    LocationConfig,
    ShotConfig,
    StyleConfig,
    RetroConfig,
    OutputFormat,
    RenderSettings,
    ProductionConfig,

    # Validation
    ValidationIssue,
    ValidationResult,

    # Execution
    ExecutionState,
    ProductionResult,
    ParallelConfig,

    # Presets
    OUTPUT_FORMAT_PRESETS,
    get_output_format_preset,
)

# Loader functions
from .production_loader import (
    load_yaml,
    save_yaml,
    load_production,
    load_production_from_dir,
    resolve_production,
    expand_shots,
    save_production,
    create_production_from_template,
    list_productions,
    get_production_info,
    estimate_production_time,
)

# Validator functions
from .production_validator import (
    validate_production,
    validate_characters,
    validate_locations,
    validate_shots,
    validate_dependencies,
    validate_timeline,
    validate_outputs,
    validate_for_execution,
)

# Execution
from .execution_engine import (
    ExecutionEngine,
    execute_production,
    resume_production,
)

# Parallel execution
from .parallel_executor import (
    DependencyGroup,
    ExecutionGraph,
    ParallelExecutor,
    BatchProcessor,
    analyze_dependencies,
    create_execution_graph,
    get_parallel_estimate,
    optimize_worker_count,
)


__all__ = [
    # Enums
    "ExecutionPhase",
    "ExecutionStatus",
    "ValidationSeverity",
    "EXECUTION_PHASES",

    # Metadata
    "ProductionMeta",

    # Configuration
    "CharacterConfig",
    "LocationConfig",
    "ShotConfig",
    "StyleConfig",
    "RetroConfig",
    "OutputFormat",
    "RenderSettings",
    "ProductionConfig",

    # Validation
    "ValidationIssue",
    "ValidationResult",

    # Execution
    "ExecutionState",
    "ProductionResult",
    "ParallelConfig",

    # Presets
    "OUTPUT_FORMAT_PRESETS",
    "get_output_format_preset",

    # Loader
    "load_yaml",
    "save_yaml",
    "load_production",
    "load_production_from_dir",
    "resolve_production",
    "expand_shots",
    "save_production",
    "create_production_from_template",
    "list_productions",
    "get_production_info",
    "estimate_production_time",

    # Validator
    "validate_production",
    "validate_characters",
    "validate_locations",
    "validate_shots",
    "validate_dependencies",
    "validate_timeline",
    "validate_outputs",
    "validate_for_execution",

    # Execution
    "ExecutionEngine",
    "execute_production",
    "resume_production",

    # Parallel
    "DependencyGroup",
    "ExecutionGraph",
    "ParallelExecutor",
    "BatchProcessor",
    "analyze_dependencies",
    "create_execution_graph",
    "get_parallel_estimate",
    "optimize_worker_count",
]


__version__ = "0.1.0"
