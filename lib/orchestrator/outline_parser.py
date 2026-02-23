"""
Scene Outline Parser

Parses scene outlines from YAML, JSON, and dictionary sources.
Validates outline structure and extracts requirements.

Implements REQ-SO-01: Scene Outline Parser.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import json

from .types import (
    SceneOutline,
    SceneDimensions,
    AssetRequirement,
    LightingRequirement,
    CameraRequirement,
    SceneTemplate,
    SCENE_TEMPLATES,
    get_template,
)


class ParseError(Exception):
    """Error parsing scene outline."""
    pass


class ValidationError(Exception):
    """Error validating scene outline."""
    pass


@dataclass
class ParseResult:
    """
    Result of parsing scene outline.

    Attributes:
        outline: Parsed scene outline (None if failed)
        errors: Parse errors encountered
        warnings: Warnings generated
        source: Source file/string
    """
    outline: Optional[SceneOutline] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    source: str = ""

    @property
    def success(self) -> bool:
        """Check if parsing succeeded."""
        return self.outline is not None and len(self.errors) == 0


class OutlineParser:
    """
    Parses scene outlines from various sources.

    Supports YAML, JSON, and dictionary inputs.
    Validates structure and fills defaults.

    Usage:
        parser = OutlineParser()
        result = parser.parse_yaml("scene.yaml")
        if result.success:
            outline = result.outline
    """

    # Required top-level keys
    REQUIRED_KEYS = []

    # Optional keys with defaults
    DEFAULTS = {
        "name": "Untitled Scene",
        "scene_type": "interior",
        "style": "photorealistic",
        "description": "",
    }

    # Valid scene types
    VALID_SCENE_TYPES = [
        "interior", "exterior", "urban", "product",
        "portrait", "environment", "mixed",
    ]

    # Valid styles
    VALID_STYLES = [
        "photorealistic", "stylized", "cartoon",
        "low_poly", "retro", "sci_fi", "fantasy", "minimalist",
    ]

    def __init__(self, strict: bool = False):
        """
        Initialize parser.

        Args:
            strict: If True, raise errors on warnings
        """
        self.strict = strict

    def parse_yaml(self, path: Union[str, Path]) -> ParseResult:
        """
        Parse scene outline from YAML file.

        Args:
            path: Path to YAML file

        Returns:
            ParseResult with outline or errors
        """
        try:
            import yaml
        except ImportError:
            return ParseResult(
                errors=["PyYAML not installed. Install with: pip install pyyaml"],
                source=str(path),
            )

        path = Path(path)
        if not path.exists():
            return ParseResult(
                errors=[f"File not found: {path}"],
                source=str(path),
            )

        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            return ParseResult(
                errors=[f"YAML parse error: {e}"],
                source=str(path),
            )
        except Exception as e:
            return ParseResult(
                errors=[f"Error reading file: {e}"],
                source=str(path),
            )

        result = self.parse_dict(data)
        result.source = str(path)
        return result

    def parse_json(self, path: Union[str, Path]) -> ParseResult:
        """
        Parse scene outline from JSON file.

        Args:
            path: Path to JSON file

        Returns:
            ParseResult with outline or errors
        """
        path = Path(path)
        if not path.exists():
            return ParseResult(
                errors=[f"File not found: {path}"],
                source=str(path),
            )

        try:
            with open(path, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return ParseResult(
                errors=[f"JSON parse error: {e}"],
                source=str(path),
            )
        except Exception as e:
            return ParseResult(
                errors=[f"Error reading file: {e}"],
                source=str(path),
            )

        result = self.parse_dict(data)
        result.source = str(path)
        return result

    def parse_json_string(self, json_str: str) -> ParseResult:
        """
        Parse scene outline from JSON string.

        Args:
            json_str: JSON string

        Returns:
            ParseResult with outline or errors
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            return ParseResult(
                errors=[f"JSON parse error: {e}"],
                source="<string>",
            )

        return self.parse_dict(data)

    def parse_dict(self, data: Dict[str, Any]) -> ParseResult:
        """
        Parse scene outline from dictionary.

        Args:
            data: Dictionary with outline data

        Returns:
            ParseResult with outline or errors
        """
        errors = []
        warnings = []

        # Check for template reference
        if "template" in data:
            template_result = self._apply_template(data)
            if template_result.errors:
                return ParseResult(
                    errors=template_result.errors,
                    warnings=template_result.warnings,
                    source="<template>",
                )
            data = template_result.outline
            warnings.extend(template_result.warnings)

        # Validate required keys
        for key in self.REQUIRED_KEYS:
            if key not in data:
                errors.append(f"Missing required key: {key}")

        # Apply defaults
        for key, default in self.DEFAULTS.items():
            if key not in data:
                data[key] = default
                warnings.append(f"Using default value for '{key}': {default}")

        # Validate scene type
        if data.get("scene_type") not in self.VALID_SCENE_TYPES:
            errors.append(
                f"Invalid scene_type: {data.get('scene_type')}. "
                f"Valid types: {', '.join(self.VALID_SCENE_TYPES)}"
            )

        # Validate style
        if data.get("style") not in self.VALID_STYLES:
            errors.append(
                f"Invalid style: {data.get('style')}. "
                f"Valid styles: {', '.join(self.VALID_STYLES)}"
            )

        if errors:
            if self.strict:
                raise ValidationError("\n".join(errors))
            return ParseResult(errors=errors, warnings=warnings)

        # Build outline
        try:
            outline = self._build_outline(data)
        except Exception as e:
            errors.append(f"Error building outline: {e}")
            return ParseResult(errors=errors, warnings=warnings)

        return ParseResult(outline=outline, warnings=warnings)

    def _apply_template(self, data: Dict[str, Any]) -> ParseResult:
        """Apply template and merge with overrides."""
        template_id = data.pop("template")
        template = get_template(template_id)

        if not template:
            return ParseResult(
                errors=[f"Template not found: {template_id}"],
                source=f"template:{template_id}",
            )

        # Start with template outline
        template_data = template.outline_template.copy()

        # Deep merge overrides
        merged = self._deep_merge(template_data, data)

        return ParseResult(outline=merged, warnings=[f"Applied template: {template_id}"])

    def _deep_merge(
        self,
        base: Dict[str, Any],
        override: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _build_outline(self, data: Dict[str, Any]) -> SceneOutline:
        """Build SceneOutline from validated data."""
        outline = SceneOutline(
            name=data.get("name", "Untitled Scene"),
            scene_type=data.get("scene_type", "interior"),
            style=data.get("style", "photorealistic"),
            description=data.get("description", ""),
            backdrop=data.get("backdrop", {}),
            custom_settings=data.get("custom_settings", {}),
            metadata=data.get("metadata", {}),
        )

        # Parse dimensions
        if "dimensions" in data:
            dim_data = data["dimensions"]
            outline.dimensions = SceneDimensions(
                width=dim_data.get("width", 20.0),
                height=dim_data.get("height", 4.0),
                depth=dim_data.get("depth", 20.0),
                unit_scale=dim_data.get("unit_scale", 1.0),
            )

        # Parse asset requirements
        if "asset_requirements" in data:
            outline.asset_requirements = [
                self._parse_asset_requirement(r)
                for r in data["asset_requirements"]
            ]

        # Parse lighting
        if "lighting" in data:
            outline.lighting = self._parse_lighting_requirement(data["lighting"])

        # Parse camera
        if "camera" in data:
            outline.camera = self._parse_camera_requirement(data["camera"])

        return outline

    def _parse_asset_requirement(self, data: Dict[str, Any]) -> AssetRequirement:
        """Parse asset requirement from dict."""
        size_constraints = data.get("size_constraints")
        if size_constraints and isinstance(size_constraints, list):
            size_constraints = tuple(size_constraints)

        return AssetRequirement(
            requirement_id=data.get("requirement_id", ""),
            category=data.get("category", "prop"),
            subcategory=data.get("subcategory", ""),
            description=data.get("description", ""),
            quantity=data.get("quantity", 1),
            priority=data.get("priority", "required"),
            style_constraints=data.get("style_constraints", []),
            size_constraints=size_constraints,
            placement_hints=data.get("placement_hints", []),
            alternatives=data.get("alternatives", []),
            metadata=data.get("metadata", {}),
        )

    def _parse_lighting_requirement(self, data: Dict[str, Any]) -> LightingRequirement:
        """Parse lighting requirement from dict."""
        return LightingRequirement(
            mood=data.get("mood", "neutral"),
            time_of_day=data.get("time_of_day", "noon"),
            weather=data.get("weather", "clear"),
            intensity=data.get("intensity", 1.0),
            use_studio_lights=data.get("use_studio_lights", False),
            studio_preset=data.get("studio_preset", "three_point"),
            use_natural_light=data.get("use_natural_light", True),
            atmospherics=data.get("atmospherics", []),
        )

    def _parse_camera_requirement(self, data: Dict[str, Any]) -> CameraRequirement:
        """Parse camera requirement from dict."""
        sensor_size = data.get("sensor_size", (36.0, 24.0))
        if isinstance(sensor_size, list):
            sensor_size = tuple(sensor_size)

        look_at_target = data.get("look_at_target")
        if look_at_target and isinstance(look_at_target, list):
            look_at_target = tuple(look_at_target)

        return CameraRequirement(
            focal_length=data.get("focal_length", 50.0),
            sensor_size=sensor_size,
            target_subject=data.get("target_subject", ""),
            framing=data.get("framing", "medium"),
            camera_movement=data.get("camera_movement", "static"),
            depth_of_field=data.get("depth_of_field"),
            look_at_target=look_at_target,
        )


def parse_outline(source: Union[str, Path, Dict[str, Any]]) -> ParseResult:
    """
    Convenience function to parse outline from any source.

    Args:
        source: Path to YAML/JSON file or dictionary

    Returns:
        ParseResult with outline or errors
    """
    parser = OutlineParser()

    if isinstance(source, dict):
        return parser.parse_dict(source)

    source = Path(source)
    if source.suffix in [".yaml", ".yml"]:
        return parser.parse_yaml(source)
    elif source.suffix == ".json":
        return parser.parse_json(source)
    else:
        return ParseResult(
            errors=[f"Unsupported file format: {source.suffix}"],
            source=str(source),
        )


def outline_to_yaml(outline: SceneOutline, path: Union[str, Path]) -> bool:
    """
    Write scene outline to YAML file.

    Args:
        outline: SceneOutline to write
        path: Output file path

    Returns:
        True if successful
    """
    try:
        import yaml
    except ImportError:
        raise ImportError("PyYAML required. Install with: pip install pyyaml")

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        yaml.dump(outline.to_dict(), f, default_flow_style=False, sort_keys=False)

    return True


def outline_to_json(outline: SceneOutline, path: Union[str, Path]) -> bool:
    """
    Write scene outline to JSON file.

    Args:
        outline: SceneOutline to write
        path: Output file path

    Returns:
        True if successful
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        json.dump(outline.to_dict(), f, indent=2)

    return True


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ParseError",
    "ValidationError",
    "ParseResult",
    "OutlineParser",
    "parse_outline",
    "outline_to_yaml",
    "outline_to_json",
]
