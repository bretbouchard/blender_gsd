"""
Tentacle Export Pipeline

Complete FBX export pipeline for Unreal Engine 5.x.

This module provides:
- LOD generation with configurable strategies
- FBX export with skeleton and morph targets
- Material zone setup for UE5
- Export presets for common configurations

Usage:
    from lib.tentacle.export import (
        # Types
        LODConfig,
        LODLevel,
        FBXExportConfig,
        MaterialSlotConfig,
        ExportResult,

        # LOD Generation
        LODGenerator,
        generate_lods,

        # FBX Export
        FBXExporter,
        export_for_unreal,

        # Convenience
        export_tentacle_package,
    )
"""

from .types import (
    # Enums
    LODStrategy,
    ExportFormat,

    # Config dataclasses
    LODConfig,
    LODLevel,
    FBXExportConfig,
    MaterialSlotConfig,
    ExportPreset,

    # Result dataclasses
    LODResult,
    ExportResult,
    MaterialSlotResult,

    # Presets
    EXPORT_PRESETS,
    get_export_preset,
    list_export_presets,
    DEFAULT_LOD_LEVELS,
)

from .lod import (
    LODGenerator,
    generate_lods,
    generate_lod_levels,
)

from .fbx import (
    FBXExporter,
    export_for_unreal,
    export_tentacle_fbx,
)

from .pipeline import (
    ExportPipeline,
    export_tentacle_package,
)


__all__ = [
    # Enums
    "LODStrategy",
    "ExportFormat",

    # Config dataclasses
    "LODConfig",
    "LODLevel",
    "FBXExportConfig",
    "MaterialSlotConfig",
    "ExportPreset",

    # Result dataclasses
    "LODResult",
    "ExportResult",
    "MaterialSlotResult",

    # Presets
    "EXPORT_PRESETS",
    "get_export_preset",
    "list_export_presets",
    "DEFAULT_LOD_LEVELS",

    # LOD Generation
    "LODGenerator",
    "generate_lods",
    "generate_lod_levels",

    # FBX Export
    "FBXExporter",
    "export_for_unreal",
    "export_tentacle_fbx",

    # Pipeline
    "ExportPipeline",
    "export_tentacle_package",
]
