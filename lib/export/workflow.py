"""
Complete game engine export workflow.

Orchestrates the full export pipeline from validation to final output.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any, Dict
from pathlib import Path

from .fbx import export_fbx_for_unreal, FBXExportConfig, FBXExportResult
from .glb import export_glb_for_web, GLBExportConfig, GLBExportResult
from .usd import export_usd, USDExportConfig, USDExportResult
from .profiles import load_export_profile, ExportProfile, ExportTarget
from .validation import validate_export, ExportValidationResult
from .textures import bake_textures, TextureBakeConfig, TextureBakeResult


@dataclass
class GameExportResult:
    """
    Complete result of game engine export workflow.

    Attributes:
        success: Whether export succeeded
        export_type: Type of export performed
        output_path: Path to exported file
        validation: Validation result
        textures: Texture bake result (if applicable)
        errors: List of error messages
        warnings: List of warning messages
    """
    success: bool = False
    export_type: str = ""
    output_path: Optional[Path] = None
    validation: Optional[ExportValidationResult] = None
    textures: Optional[TextureBakeResult] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class GameExportWorkflow:
    """
    Complete workflow for game engine export.

    Orchestrates validation, texture baking, and export.

    Example:
        >>> workflow = GameExportWorkflow(target="unreal_5")
        >>> workflow.set_objects(selected_objects)
        >>> workflow.validate()
        >>> result = workflow.export()
    """

    def __init__(
        self,
        target: str = "unreal_5",
        profile: Optional[ExportProfile] = None,
    ):
        """
        Initialize workflow.

        Args:
            target: Target platform name
            profile: Export profile (loaded by name if not provided)
        """
        self.target = target
        self.profile = profile or load_export_profile(f"{target}_high")
        self.objects: List[Any] = []
        self._validation_result: Optional[ExportValidationResult] = None
        self._texture_result: Optional[TextureBakeResult] = None

    def set_objects(self, objects: List[Any]) -> 'GameExportWorkflow':
        """Set objects to export."""
        self.objects = objects
        return self

    def validate(
        self,
        target_poly_count: Optional[int] = None,
        max_bones_per_vertex: int = 4,
    ) -> ExportValidationResult:
        """Validate objects for export."""
        self._validation_result = validate_export(
            self.objects,
            target_poly_count=target_poly_count,
            max_bone_count=max_bones_per_vertex,
        )
        return self._validation_result

    def bake_textures(
        self,
        config: Optional[TextureBakeConfig] = None,
    ) -> TextureBakeResult:
        """Bake textures for export."""
        self._texture_result = bake_textures(self.objects, config)
        return self._texture_result

    def export(
        self,
        output_path: Optional[str] = None,
    ) -> GameExportResult:
        """
        Execute export based on profile.

        Args:
            output_path: Output path (uses profile default if not provided)

        Returns:
            GameExportResult with export status
        """
        result = GameExportResult()

        if not self.objects:
            result.errors.append("No objects set for export")
            return result

        # Determine export type based on profile format
        if self.profile.format == "fbx":
            config = FBXExportConfig(
                name=self.profile.name,
                output_path=output_path,
                scale_factor=self.profile.scale_factor,
            )
            export_result = export_fbx_for_unreal(config, self.objects)
            result.export_type = "fbx"
            result.output_path = export_result.output_path
            result.errors.extend(export_result.errors)
            result.warnings.extend(export_result.warnings)
            result.success = export_result.success

        elif self.profile.format == "glb":
            config = GLBExportConfig(
                name=self.profile.name,
                output_path=output_path,
                draco_compression=self.profile.draco_compression,
                draco_compression_level=self.profile.draco_level,
            )
            export_result = export_glb_for_web(config, self.objects)
            result.export_type = "glb"
            result.output_path = export_result.output_path
            result.errors.extend(export_result.errors)
            result.warnings.extend(export_result.warnings)
            result.success = export_result.success

        elif self.profile.format == "usd":
            config = USDExportConfig(
                name=self.profile.name,
                output_path=output_path,
            )
            export_result = export_usd(config, self.objects)
            result.export_type = "usd"
            result.output_path = export_result.output_path
            result.errors.extend(export_result.errors)
            result.warnings.extend(export_result.warnings)
            result.success = export_result.success

        else:
            result.errors.append(f"Unknown export format: {self.profile.format}")
            return result

        result.validation = self._validation_result
        result.textures = self._texture_result

        return result


def export_for_game_engine(
    objects: List[Any],
    target: str = "unreal_5",
    output_path: Optional[str] = None,
    validate_first: bool = True,
    target_poly_count: Optional[int] = None,
) -> GameExportResult:
    """
    Convenience function for complete game engine export.

    Args:
        objects: Objects to export
        target: Target platform name
        output_path: Output path
        validate_first: Whether to validate before export
        target_poly_count: Maximum polygon count for validation

    Returns:
        GameExportResult with export status

    Example:
        >>> result = export_for_game_engine(
        ...     selected_objects,
        ...     target="unreal_5",
        ...     output_path="//exports/character.fbx",
        ... )
        >>> if result.success:
        ...     print(f"Exported to {result.output_path}")
    """
    workflow = GameExportWorkflow(target=target)
    workflow.set_objects(objects)

    if validate_first:
        validation = workflow.validate(target_poly_count=target_poly_count)
        if not validation.valid:
            return GameExportResult(
                success=False,
                export_type="validation_failed",
                validation=validation,
                errors=["Validation failed - see validation.issues for details"],
            )

    return workflow.export(output_path)
