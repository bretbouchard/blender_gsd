"""
Validation Engine

Automated validation for scene generation quality assurance.
Checks scale, materials, lighting, and other quality metrics.

Implements REQ-QA-01: Automated Validation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Callable
from enum import Enum
import json
from datetime import datetime


class ValidationLevel(Enum):
    """Validation severity level."""
    ERROR = "error"         # Must fix
    WARNING = "warning"     # Should fix
    INFO = "info"           # Nice to have
    PASS = "pass"           # Validation passed


class ValidationCategory(Enum):
    """Validation category."""
    SCALE = "scale"
    MATERIALS = "materials"
    LIGHTING = "lighting"
    GEOMETRY = "geometry"
    NAMING = "naming"
    PERFORMANCE = "performance"
    RENDER = "render"
    COMPOSITION = "composition"


# =============================================================================
# VALIDATION THRESHOLDS
# =============================================================================

VALIDATION_THRESHOLDS: Dict[str, Dict[str, Any]] = {
    "scale": {
        "min_object_size": 0.001,      # 1mm
        "max_object_size": 1000.0,     # 1km
        "scene_unit_scale": 1.0,       # Meters
        "reference_height": 1.75,      # Human height
    },
    "materials": {
        "max_material_count": 100,
        "require_uv": True,
        "max_texture_size": 8192,
        "check_missing_textures": True,
    },
    "lighting": {
        "min_light_count": 1,
        "max_light_count": 50,
        "min_intensity": 0.1,
        "max_intensity": 10000.0,
    },
    "geometry": {
        "max_poly_count": 10000000,    # 10M polygons
        "max_vertices_per_object": 1000000,
        "check_manifold": True,
        "check_degenerate": True,
    },
    "performance": {
        "max_draw_calls": 5000,
        "max_memory_mb": 8192,
        "target_fps": 30,
    },
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ValidationResult:
    """
    Single validation result.

    Attributes:
        check_id: Unique check identifier
        category: Validation category
        level: Severity level
        message: Human-readable message
        object_name: Affected object name
        actual_value: Actual measured value
        expected_value: Expected value
        suggestion: Fix suggestion
        auto_fix_available: Whether auto-fix is possible
    """
    check_id: str = ""
    category: str = "geometry"
    level: str = "pass"
    message: str = ""
    object_name: str = ""
    actual_value: Any = None
    expected_value: Any = None
    suggestion: str = ""
    auto_fix_available: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "check_id": self.check_id,
            "category": self.category,
            "level": self.level,
            "message": self.message,
            "object_name": self.object_name,
            "actual_value": self.actual_value,
            "expected_value": self.expected_value,
            "suggestion": self.suggestion,
            "auto_fix_available": self.auto_fix_available,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValidationResult":
        """Create from dictionary."""
        return cls(
            check_id=data.get("check_id", ""),
            category=data.get("category", "geometry"),
            level=data.get("level", "pass"),
            message=data.get("message", ""),
            object_name=data.get("object_name", ""),
            actual_value=data.get("actual_value"),
            expected_value=data.get("expected_value"),
            suggestion=data.get("suggestion", ""),
            auto_fix_available=data.get("auto_fix_available", False),
        )


@dataclass
class ValidationReport:
    """
    Complete validation report.

    Attributes:
        report_id: Unique report identifier
        scene_name: Scene being validated
        timestamp: Validation timestamp
        results: All validation results
        summary: Summary statistics
        metadata: Additional metadata
    """
    report_id: str = ""
    scene_name: str = ""
    timestamp: str = ""
    results: List[ValidationResult] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "report_id": self.report_id,
            "scene_name": self.scene_name,
            "timestamp": self.timestamp,
            "results": [r.to_dict() for r in self.results],
            "summary": self.summary,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValidationReport":
        """Create from dictionary."""
        return cls(
            report_id=data.get("report_id", ""),
            scene_name=data.get("scene_name", ""),
            timestamp=data.get("timestamp", ""),
            results=[ValidationResult.from_dict(r) for r in data.get("results", [])],
            summary=data.get("summary", {}),
            metadata=data.get("metadata", {}),
        )

    @property
    def pass_count(self) -> int:
        """Count of passed checks."""
        return sum(1 for r in self.results if r.level == "pass")

    @property
    def error_count(self) -> int:
        """Count of errors."""
        return sum(1 for r in self.results if r.level == "error")

    @property
    def warning_count(self) -> int:
        """Count of warnings."""
        return sum(1 for r in self.results if r.level == "warning")

    @property
    def info_count(self) -> int:
        """Count of info messages."""
        return sum(1 for r in self.results if r.level == "info")

    @property
    def is_valid(self) -> bool:
        """Whether scene passed validation."""
        return self.error_count == 0


# =============================================================================
# VALIDATION ENGINE
# =============================================================================

class ValidationEngine:
    """
    Automated validation engine.

    Runs configurable validation checks on scene data.

    Usage:
        engine = ValidationEngine()
        engine.register_check("scale_check", check_scale)
        report = engine.validate_scene(scene_data)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize validation engine.

        Args:
            config: Validation configuration
        """
        self.config = config or VALIDATION_THRESHOLDS
        self._checks: Dict[str, Callable] = {}
        self._report_counter = 0

        # Register default checks
        self._register_default_checks()

    def _register_default_checks(self) -> None:
        """Register built-in validation checks."""
        self.register_check("scale_range", self._check_scale_range)
        self.register_check("material_count", self._check_material_count)
        self.register_check("lighting_basic", self._check_lighting)
        self.register_check("geometry_polycount", self._check_polycount)
        self.register_check("naming_convention", self._check_naming)

    def register_check(
        self,
        check_id: str,
        check_func: Callable[[Dict[str, Any]], List[ValidationResult]],
    ) -> None:
        """
        Register validation check.

        Args:
            check_id: Unique check identifier
            check_func: Check function that takes scene data
        """
        self._checks[check_id] = check_func

    def unregister_check(self, check_id: str) -> bool:
        """Remove validation check."""
        if check_id in self._checks:
            del self._checks[check_id]
            return True
        return False

    def validate_scene(
        self,
        scene_data: Dict[str, Any],
        checks: Optional[List[str]] = None,
        scene_name: str = "",
    ) -> ValidationReport:
        """
        Run validation on scene.

        Args:
            scene_data: Scene data to validate
            checks: Specific checks to run (all if None)
            scene_name: Scene name for report

        Returns:
            ValidationReport
        """
        self._report_counter += 1
        report = ValidationReport(
            report_id=f"val_{self._report_counter:06d}",
            scene_name=scene_name,
            timestamp=datetime.now().isoformat(),
        )

        # Determine which checks to run
        check_ids = checks if checks else list(self._checks.keys())

        # Run each check
        for check_id in check_ids:
            if check_id in self._checks:
                try:
                    results = self._checks[check_id](scene_data)
                    report.results.extend(results)
                except Exception as e:
                    report.results.append(ValidationResult(
                        check_id=check_id,
                        category="error",
                        level="error",
                        message=f"Check failed: {str(e)}",
                    ))

        # Calculate summary
        report.summary = {
            "total": len(report.results),
            "pass": report.pass_count,
            "error": report.error_count,
            "warning": report.warning_count,
            "info": report.info_count,
        }

        return report

    def _check_scale_range(self, scene_data: Dict[str, Any]) -> List[ValidationResult]:
        """Check object scale ranges."""
        results = []
        thresholds = self.config.get("scale", {})
        min_size = thresholds.get("min_object_size", 0.001)
        max_size = thresholds.get("max_object_size", 1000.0)

        objects = scene_data.get("objects", [])
        for obj in objects:
            name = obj.get("name", "unknown")
            dimensions = obj.get("dimensions", [1.0, 1.0, 1.0])
            max_dim = max(dimensions) if dimensions else 0

            if max_dim < min_size:
                results.append(ValidationResult(
                    check_id="scale_range",
                    category="scale",
                    level="warning",
                    message=f"Object too small",
                    object_name=name,
                    actual_value=max_dim,
                    expected_value=f">= {min_size}",
                    suggestion="Check if scale is correct or merge with parent",
                ))
            elif max_dim > max_size:
                results.append(ValidationResult(
                    check_id="scale_range",
                    category="scale",
                    level="warning",
                    message=f"Object very large",
                    object_name=name,
                    actual_value=max_dim,
                    expected_value=f"<= {max_size}",
                    suggestion="Check if scale is correct",
                ))
            else:
                results.append(ValidationResult(
                    check_id="scale_range",
                    category="scale",
                    level="pass",
                    message=f"Scale OK",
                    object_name=name,
                ))

        return results

    def _check_material_count(self, scene_data: Dict[str, Any]) -> List[ValidationResult]:
        """Check material count."""
        results = []
        thresholds = self.config.get("materials", {})
        max_count = thresholds.get("max_material_count", 100)

        materials = scene_data.get("materials", [])
        count = len(materials)

        if count > max_count:
            results.append(ValidationResult(
                check_id="material_count",
                category="materials",
                level="warning",
                message="Too many materials",
                actual_value=count,
                expected_value=f"<= {max_count}",
                suggestion="Merge similar materials to reduce count",
            ))
        else:
            results.append(ValidationResult(
                check_id="material_count",
                category="materials",
                level="pass",
                message=f"Material count OK ({count})",
                actual_value=count,
            ))

        return results

    def _check_lighting(self, scene_data: Dict[str, Any]) -> List[ValidationResult]:
        """Check lighting configuration."""
        results = []
        thresholds = self.config.get("lighting", {})
        min_lights = thresholds.get("min_light_count", 1)
        max_lights = thresholds.get("max_light_count", 50)

        lights = scene_data.get("lights", [])
        count = len(lights)

        if count < min_lights:
            results.append(ValidationResult(
                check_id="lighting_basic",
                category="lighting",
                level="error",
                message="No lights in scene",
                actual_value=count,
                expected_value=f">= {min_lights}",
                suggestion="Add at least one light source",
            ))
        elif count > max_lights:
            results.append(ValidationResult(
                check_id="lighting_basic",
                category="lighting",
                level="warning",
                message="Many lights may impact performance",
                actual_value=count,
                expected_value=f"<= {max_lights}",
                suggestion="Consider using light linking or fewer lights",
            ))
        else:
            results.append(ValidationResult(
                check_id="lighting_basic",
                category="lighting",
                level="pass",
                message=f"Light count OK ({count})",
                actual_value=count,
            ))

        return results

    def _check_polycount(self, scene_data: Dict[str, Any]) -> List[ValidationResult]:
        """Check polygon count."""
        results = []
        thresholds = self.config.get("geometry", {})
        max_polys = thresholds.get("max_poly_count", 10000000)

        total_polys = scene_data.get("total_polygons", 0)

        if total_polys > max_polys:
            results.append(ValidationResult(
                check_id="geometry_polycount",
                category="geometry",
                level="warning",
                message="High polygon count",
                actual_value=total_polys,
                expected_value=f"<= {max_polys}",
                suggestion="Use LOD system or decimate",
            ))
        else:
            results.append(ValidationResult(
                check_id="geometry_polycount",
                category="geometry",
                level="pass",
                message=f"Polygon count OK ({total_polys:,})",
                actual_value=total_polys,
            ))

        return results

    def _check_naming(self, scene_data: Dict[str, Any]) -> List[ValidationResult]:
        """Check naming conventions."""
        results = []

        objects = scene_data.get("objects", [])
        for obj in objects:
            name = obj.get("name", "")

            # Check for common naming issues
            if name.startswith("."):
                results.append(ValidationResult(
                    check_id="naming_convention",
                    category="naming",
                    level="info",
                    message="Object starts with dot (hidden)",
                    object_name=name,
                    suggestion="Consider renaming if not intentional",
                ))
            elif " " in name:
                results.append(ValidationResult(
                    check_id="naming_convention",
                    category="naming",
                    level="info",
                    message="Object name contains spaces",
                    object_name=name,
                    suggestion="Use underscores instead of spaces",
                ))
            elif name:
                results.append(ValidationResult(
                    check_id="naming_convention",
                    category="naming",
                    level="pass",
                    message="Naming OK",
                    object_name=name,
                ))

        return results

    def set_threshold(self, category: str, key: str, value: Any) -> None:
        """Set validation threshold."""
        if category not in self.config:
            self.config[category] = {}
        self.config[category][key] = value

    def get_threshold(self, category: str, key: str, default: Any = None) -> Any:
        """Get validation threshold."""
        return self.config.get(category, {}).get(key, default)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def validate_scene(
    scene_data: Dict[str, Any],
    checks: Optional[List[str]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> ValidationReport:
    """
    Convenience function for scene validation.

    Args:
        scene_data: Scene data to validate
        checks: Specific checks to run
        config: Validation configuration

    Returns:
        ValidationReport
    """
    engine = ValidationEngine(config)
    return engine.validate_scene(scene_data, checks)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "ValidationLevel",
    "ValidationCategory",
    # Constants
    "VALIDATION_THRESHOLDS",
    # Data classes
    "ValidationResult",
    "ValidationReport",
    # Classes
    "ValidationEngine",
    # Functions
    "validate_scene",
]
