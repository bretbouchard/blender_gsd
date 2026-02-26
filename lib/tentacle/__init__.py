"""
Tentacle System - Procedural generation for organic tentacles.

Primary use case: Zombie mouth tentacles for horror characters.

This module provides:
- Core data types for tentacle configuration
- YAML preset loading with caching
- Taper profile calculations
- Zombie mouth multi-tentacle configurations
- Animation system with shape keys and state machines
- Procedural materials with horror themes
- FBX export pipeline for Unreal Engine 5.x

Usage:
    from lib.tentacle import (
        # Types
        TentacleConfig,
        TaperProfile,
        SegmentConfig,
        ZombieMouthConfig,

        # Presets
        TentaclePresetLoader,
        load_tentacle,
        load_zombie_mouth,

        # Animation
        ShapeKeyPreset,
        AnimationState,
        ShapeKeyGenerator,
        TentacleStateMachine,
        MultiTentacleStateCoordinator,

        # Materials
        MaterialTheme,
        ThemePreset,
        SkinShaderGenerator,
        create_skin_material,

        # Export
        LODGenerator,
        FBXExporter,
        ExportPipeline,
        export_for_unreal,

        # Version
        __version__
    )
"""

from .types import (
    TentacleConfig,
    TaperProfile,
    SegmentConfig,
    ZombieMouthConfig,
    sanitize_blender_name,
)

from .presets import (
    TentaclePresetLoader,
    load_tentacle,
    load_zombie_mouth,
    list_tentacle_presets,
    list_zombie_mouth_presets,
)

from .animation import (
    # Enums
    ShapeKeyPreset,
    AnimationState,
    # Config dataclasses
    ShapeKeyConfig,
    StateTransition,
    AnimationStateConfig,
    SplineIKRig,
    RigConfig,
    # Result dataclasses
    ShapeKeyResult,
    RigResult,
    # Shape key generation
    ShapeKeyGenerator,
    get_preset_config,
    SHAPE_KEY_PRESETS,
    # State machine
    TentacleStateMachine,
    MultiTentacleStateCoordinator,
    DEFAULT_STATE_CONFIGS,
    DEFAULT_TRANSITIONS,
)

from .materials import (
    # Enums
    MaterialTheme,
    WetnessLevel,
    # Config dataclasses
    SSSConfig,
    WetnessConfig,
    VeinConfig,
    RoughnessConfig,
    MaterialZone,
    ThemePreset,
    TentacleMaterialConfig,
    BakeConfig,
    BakeResult,
    # Theme presets
    THEME_PRESETS,
    get_theme_preset,
    get_theme_preset_by_name,
    list_theme_presets,
    blend_themes,
    # Skin shader
    SkinShaderGenerator,
    create_skin_material,
    # Vein patterns
    VeinPatternGenerator,
    create_bioluminescent_pattern,
    # Baking
    TextureBaker,
    bake_material,
    bake_all_lods,
    # Convenience
    create_horror_material,
    create_zombie_tentacle_material,
)

from .export import (
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
    # LOD Generation
    LODGenerator,
    generate_lods,
    generate_lod_levels,
    # FBX Export
    FBXExporter,
    export_for_unreal,
    export_tentacle_fbx,
    # Pipeline
    ExportPipeline,
    export_tentacle_package,
    # Presets
    EXPORT_PRESETS,
    get_export_preset,
    list_export_presets,
    DEFAULT_LOD_LEVELS,
)


__version__ = "1.0.0"
VERSION = __version__  # Alias for backwards compatibility


__all__ = [
    # Types
    "TentacleConfig",
    "TaperProfile",
    "SegmentConfig",
    "ZombieMouthConfig",
    "sanitize_blender_name",
    # Presets
    "TentaclePresetLoader",
    "load_tentacle",
    "load_zombie_mouth",
    "list_tentacle_presets",
    "list_zombie_mouth_presets",
    # Animation - Enums
    "ShapeKeyPreset",
    "AnimationState",
    # Animation - Config dataclasses
    "ShapeKeyConfig",
    "StateTransition",
    "AnimationStateConfig",
    "SplineIKRig",
    "RigConfig",
    # Animation - Result dataclasses
    "ShapeKeyResult",
    "RigResult",
    # Animation - Shape key generation
    "ShapeKeyGenerator",
    "get_preset_config",
    "SHAPE_KEY_PRESETS",
    # Animation - State machine
    "TentacleStateMachine",
    "MultiTentacleStateCoordinator",
    "DEFAULT_STATE_CONFIGS",
    "DEFAULT_TRANSITIONS",
    # Materials - Enums
    "MaterialTheme",
    "WetnessLevel",
    # Materials - Config dataclasses
    "SSSConfig",
    "WetnessConfig",
    "VeinConfig",
    "RoughnessConfig",
    "MaterialZone",
    "ThemePreset",
    "TentacleMaterialConfig",
    "BakeConfig",
    "BakeResult",
    # Materials - Theme presets
    "THEME_PRESETS",
    "get_theme_preset",
    "get_theme_preset_by_name",
    "list_theme_presets",
    "blend_themes",
    # Materials - Skin shader
    "SkinShaderGenerator",
    "create_skin_material",
    # Materials - Vein patterns
    "VeinPatternGenerator",
    "create_bioluminescent_pattern",
    # Materials - Baking
    "TextureBaker",
    "bake_material",
    "bake_all_lods",
    # Materials - Convenience
    "create_horror_material",
    "create_zombie_tentacle_material",
    # Export - Enums
    "LODStrategy",
    "ExportFormat",
    # Export - Config dataclasses
    "LODConfig",
    "LODLevel",
    "FBXExportConfig",
    "MaterialSlotConfig",
    "ExportPreset",
    # Export - Result dataclasses
    "LODResult",
    "ExportResult",
    "MaterialSlotResult",
    # Export - LOD Generation
    "LODGenerator",
    "generate_lods",
    "generate_lod_levels",
    # Export - FBX Export
    "FBXExporter",
    "export_for_unreal",
    "export_tentacle_fbx",
    # Export - Pipeline
    "ExportPipeline",
    "export_tentacle_package",
    # Export - Presets
    "EXPORT_PRESETS",
    "get_export_preset",
    "list_export_presets",
    "DEFAULT_LOD_LEVELS",
    # Version
    "__version__",
    "VERSION",
]
