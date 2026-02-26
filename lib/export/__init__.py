"""
Game Engine Export Pipeline forProvides FBX, GLB, and USD export functionality for exporting Blender content to game engines ( real-time applications.

Key Components:
- FBX export for Unreal Engine 5.x
- GLB export for web/AR/VR/GPU applications
- USD export for modern pipelines
- Export profiles system for- Texture baking integration
- Validation utilities

Example:
    >>> from lib.export import (
        ...     export_fbx_for_unreal,
        ...     export_glb_for_web,
        ...     load_export_profile,
        ... )
    >>> # Export scene for    >>> result = export_fbx_for_unreal(
    ...     result = export_glb_for_web(
    ...     if result.success:
    ...         print(f"Exported to {result.output_path}")
"""

__version__ = "0.1.0"
__author__ = "Blender GSD Team"

from .fbx import (
    export_fbx_for_unreal,
    FBXExportConfig,
    FBXExportResult,
)
from .glb import (
    export_glb_for_web,
    GLBExportConfig,
    GLBExportResult,
)
from .usd import (
    export_usd,
    USDExportConfig,
    USDExportResult,
)
from .profiles import (
    load_export_profile,
    save_export_profile,
    ExportProfile,
    ExportTarget,
)
from .validation import (
    validate_export,
    ExportValidationResult,
    ValidationResult,
)
from .textures import (
    bake_textures,
    TextureBakeConfig,
    TextureBakeResult,
)
from .workflow import (
    GameExportWorkflow,
    export_for_game_engine,
)

__all__ = [
    # Version
    "__version__",
    # FBX
    "export_fbx_for_unreal",
    "FBXExportConfig",
    "FBXExportResult",
    # GLB
    "export_glb_for_web",
    "GLBExportConfig",
    "GLBExportResult",
    # USD
    "export_usd",
    "USDExportConfig",
    "USDExportResult",
    # Profiles
    "load_export_profile",
    "save_export_profile",
    "ExportProfile",
    "ExportTarget",
    # Validation
    "validate_export",
    "ExportValidationResult",
    "ValidationResult",
    # Textures
    "bake_textures",
    "TextureBakeConfig",
    "TextureBakeResult",
    # Workflow
    "GameExportWorkflow",
    "export_for_game_engine",
]
