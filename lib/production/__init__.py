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
- REQ-CONFIG-01 through REQ-CONFIG-06: Master config support

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

    # Or use master config (Phase 14.2)
    from lib.production import (
        MasterProductionConfig,
        expand_shot_templates,
        get_production_summary,
    )

    config = MasterProductionConfig.from_yaml("production.yaml")
    summary = get_production_summary(config)

Part of Phase 14.1: Production Orchestrator
Part of Phase 14.2: Master Production Config
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

# Master config (Phase 14.2)
from .config_schema import (
    # Types
    OutputCodec,
    DitherMode,
    SourceConfig,
    CharacterDef,
    LocationDef,
    ShotDef,
    RetroOutputConfig,
    OutputDef,
    MasterProductionConfig,
    MASTER_CONFIG_PRESETS,
    create_master_config_from_preset,
)

from .template_expansion import (
    # Types
    CompleteShotConfig,
    # Constants
    SHOT_TEMPLATES,
    STYLE_PRESETS,
    # Functions
    expand_shot_templates,
    resolve_character_wardrobe,
    resolve_location,
    apply_style_preset,
    get_shot_template,
    list_shot_templates,
    list_style_presets,
    suggest_shot_for_context,
    expand_output_formats,
    get_production_summary,
)

from .config_validation import (
    validate_master_config,
    validate_meta,
    validate_source,
    validate_character_defs,
    validate_location_defs,
    validate_shot_defs,
    check_file_references,
    check_character_models,
    check_location_presets,
    check_shot_templates,
    validate_output_defs,
    validate_for_execution_strict,
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

    # Master config (Phase 14.2)
    "OutputCodec",
    "DitherMode",
    "SourceConfig",
    "CharacterDef",
    "LocationDef",
    "ShotDef",
    "RetroOutputConfig",
    "OutputDef",
    "MasterProductionConfig",
    "MASTER_CONFIG_PRESETS",
    "create_master_config_from_preset",

    # Template expansion
    "CompleteShotConfig",
    "SHOT_TEMPLATES",
    "STYLE_PRESETS",
    "expand_shot_templates",
    "resolve_character_wardrobe",
    "resolve_location",
    "apply_style_preset",
    "get_shot_template",
    "list_shot_templates",
    "list_style_presets",
    "suggest_shot_for_context",
    "expand_output_formats",
    "get_production_summary",

    # Config validation
    "validate_master_config",
    "validate_meta",
    "validate_source",
    "validate_character_defs",
    "validate_location_defs",
    "validate_shot_defs",
    "check_file_references",
    "check_character_models",
    "check_location_presets",
    "check_shot_templates",
    "validate_output_defs",
    "validate_for_execution_strict",
]


__version__ = "0.2.0"
