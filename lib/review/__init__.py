"""
Review Module

Automated validation, visual comparison, and approval workflow
for scene generation quality assurance.

Implements REQ-QA-01 through REQ-QA-06.

Features:
- Automated validation (scale, materials, lighting)
- Visual comparison (before/after, reference)
- Checklist system
- Report generation (HTML, PDF)
- Approval workflow (pending, approved, revision)
- Version history

Usage:
    from lib.review import (
        ValidationEngine,
        ComparisonTool,
        ChecklistManager,
        ReportGenerator,
        ApprovalWorkflow,
    )

    # Validate scene
    engine = ValidationEngine()
    results = engine.validate_scene(scene_data)

    # Generate report
    report = ReportGenerator()
    report.generate_html(results, "validation_report.html")
"""

from __future__ import annotations

__all__ = [
    # Enums
    "ValidationLevel",
    "ValidationCategory",
    "ApprovalStatus",
    "ReportFormat",
    # Data classes
    "ValidationResult",
    "ValidationReport",
    "ComparisonResult",
    "ChecklistItem",
    "Checklist",
    "ApprovalRecord",
    # Classes
    "ValidationEngine",
    "ComparisonTool",
    "ChecklistManager",
    "ReportGenerator",
    "ApprovalWorkflow",
    # Functions
    "validate_scene",
    "generate_report",
]

__version__ = "1.0.0"
__author__ = "Blender GSD Project"


from .validation import (
    # Enums
    ValidationLevel,
    ValidationCategory,
    # Data classes
    ValidationResult,
    ValidationReport,
    # Classes
    ValidationEngine,
    # Functions
    validate_scene,
)

from .comparison import (
    # Data classes
    ComparisonResult,
    # Classes
    ComparisonTool,
)

from .checklists import (
    # Data classes
    ChecklistItem,
    Checklist,
    # Classes
    ChecklistManager,
)

from .reports import (
    # Enums
    ReportFormat,
    # Classes
    ReportGenerator,
    # Functions
    generate_report,
)

from .workflow import (
    # Enums
    ApprovalStatus,
    # Data classes
    ApprovalRecord,
    # Classes
    ApprovalWorkflow,
)
