"""
Checklist System

Completion verification and quality checklists.

Implements REQ-QA-03: Checklist System.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
from pathlib import Path
import json
from datetime import datetime


class ChecklistStatus(Enum):
    """Checklist item status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ChecklistItem:
    """
    Single checklist item.

    Attributes:
        item_id: Unique item identifier
        name: Item name
        description: Item description
        category: Category for grouping
        status: Current status
        required: Whether item is required
        auto_check: Whether item can be auto-checked
        check_function: Function name for auto-check
        notes: Additional notes
        completed_by: Who completed the item
        completed_at: When item was completed
    """
    item_id: str = ""
    name: str = ""
    description: str = ""
    category: str = "general"
    status: str = "pending"
    required: bool = True
    auto_check: bool = False
    check_function: str = ""
    notes: str = ""
    completed_by: str = ""
    completed_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "item_id": self.item_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "status": self.status,
            "required": self.required,
            "auto_check": self.auto_check,
            "check_function": self.check_function,
            "notes": self.notes,
            "completed_by": self.completed_by,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChecklistItem":
        """Create from dictionary."""
        return cls(
            item_id=data.get("item_id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            category=data.get("category", "general"),
            status=data.get("status", "pending"),
            required=data.get("required", True),
            auto_check=data.get("auto_check", False),
            check_function=data.get("check_function", ""),
            notes=data.get("notes", ""),
            completed_by=data.get("completed_by", ""),
            completed_at=data.get("completed_at", ""),
        )


@dataclass
class Checklist:
    """
    Complete checklist.

    Attributes:
        checklist_id: Unique checklist identifier
        name: Checklist name
        description: Checklist description
        items: All checklist items
        created_at: Creation timestamp
        updated_at: Last update timestamp
        metadata: Additional metadata
    """
    checklist_id: str = ""
    name: str = ""
    description: str = ""
    items: List[ChecklistItem] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "checklist_id": self.checklist_id,
            "name": self.name,
            "description": self.description,
            "items": [i.to_dict() for i in self.items],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checklist":
        """Create from dictionary."""
        return cls(
            checklist_id=data.get("checklist_id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            items=[ChecklistItem.from_dict(i) for i in data.get("items", [])],
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            metadata=data.get("metadata", {}),
        )

    @property
    def total_items(self) -> int:
        """Total number of items."""
        return len(self.items)

    @property
    def completed_count(self) -> int:
        """Number of completed items."""
        return sum(1 for i in self.items if i.status == "completed")

    @property
    def required_completed(self) -> int:
        """Number of completed required items."""
        return sum(
            1 for i in self.items
            if i.required and i.status == "completed"
        )

    @property
    def required_total(self) -> int:
        """Total required items."""
        return sum(1 for i in self.items if i.required)

    @property
    def completion_percentage(self) -> float:
        """Overall completion percentage."""
        if not self.items:
            return 0.0
        return (self.completed_count / self.total_items) * 100

    @property
    def is_complete(self) -> bool:
        """Whether all required items are complete."""
        return self.required_completed == self.required_total


# =============================================================================
# PREDEFINED CHECKLISTS
# =============================================================================

SCENE_PRODUCTION_CHECKLIST: List[Dict[str, Any]] = [
    {
        "item_id": "scale_check",
        "name": "Scale Verification",
        "description": "All objects at correct scale",
        "category": "geometry",
        "required": True,
        "auto_check": True,
        "check_function": "validate_scale",
    },
    {
        "item_id": "material_assignment",
        "name": "Material Assignment",
        "description": "All objects have materials assigned",
        "category": "materials",
        "required": True,
        "auto_check": True,
        "check_function": "validate_materials",
    },
    {
        "item_id": "lighting_setup",
        "name": "Lighting Setup",
        "description": "Scene has proper lighting",
        "category": "lighting",
        "required": True,
        "auto_check": True,
        "check_function": "validate_lighting",
    },
    {
        "item_id": "camera_animation",
        "name": "Camera Animation",
        "description": "Camera moves are smooth",
        "category": "animation",
        "required": False,
        "auto_check": False,
    },
    {
        "item_id": "render_settings",
        "name": "Render Settings",
        "description": "Render settings are production-ready",
        "category": "render",
        "required": True,
        "auto_check": True,
        "check_function": "validate_render_settings",
    },
    {
        "item_id": "export_test",
        "name": "Export Test",
        "description": "Scene exports correctly",
        "category": "export",
        "required": True,
        "auto_check": False,
    },
    {
        "item_id": "frame_range",
        "name": "Frame Range",
        "description": "Frame range is set correctly",
        "category": "animation",
        "required": True,
        "auto_check": True,
        "check_function": "validate_frame_range",
    },
    {
        "item_id": "file_naming",
        "name": "File Naming",
        "description": "Output files follow naming convention",
        "category": "organization",
        "required": True,
        "auto_check": True,
        "check_function": "validate_naming",
    },
]


# =============================================================================
# CHECKLIST MANAGER
# =============================================================================

class ChecklistManager:
    """
    Manages checklists and verification.

    Usage:
        manager = ChecklistManager()
        checklist = manager.create_checklist("Scene Review", SCENE_PRODUCTION_CHECKLIST)
        manager.check_item(checklist.checklist_id, "scale_check", "completed")
    """

    def __init__(self):
        """Initialize checklist manager."""
        self.checklists: Dict[str, Checklist] = {}
        self._checklist_counter = 0

    def create_checklist(
        self,
        name: str,
        items: Optional[List[Dict[str, Any]]] = None,
        description: str = "",
    ) -> Checklist:
        """
        Create new checklist.

        Args:
            name: Checklist name
            items: Initial items
            description: Checklist description

        Returns:
            Created Checklist
        """
        self._checklist_counter += 1
        checklist_id = f"check_{self._checklist_counter:06d}"

        checklist = Checklist(
            checklist_id=checklist_id,
            name=name,
            description=description,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

        if items:
            for idx, item_data in enumerate(items):
                item = ChecklistItem(
                    item_id=item_data.get("item_id", f"item_{idx:03d}"),
                    name=item_data.get("name", ""),
                    description=item_data.get("description", ""),
                    category=item_data.get("category", "general"),
                    required=item_data.get("required", True),
                    auto_check=item_data.get("auto_check", False),
                    check_function=item_data.get("check_function", ""),
                )
                checklist.items.append(item)

        self.checklists[checklist_id] = checklist
        return checklist

    def get_checklist(self, checklist_id: str) -> Optional[Checklist]:
        """Get checklist by ID."""
        return self.checklists.get(checklist_id)

    def check_item(
        self,
        checklist_id: str,
        item_id: str,
        status: str,
        notes: str = "",
        completed_by: str = "",
    ) -> bool:
        """
        Update item status.

        Args:
            checklist_id: Checklist ID
            item_id: Item ID
            status: New status
            notes: Optional notes
            completed_by: Who completed

        Returns:
            Success status
        """
        checklist = self.checklists.get(checklist_id)
        if not checklist:
            return False

        for item in checklist.items:
            if item.item_id == item_id:
                item.status = status
                item.notes = notes
                if status == "completed":
                    item.completed_by = completed_by
                    item.completed_at = datetime.now().isoformat()
                checklist.updated_at = datetime.now().isoformat()
                return True

        return False

    def add_item(
        self,
        checklist_id: str,
        item: ChecklistItem,
    ) -> bool:
        """Add item to checklist."""
        checklist = self.checklists.get(checklist_id)
        if not checklist:
            return False

        checklist.items.append(item)
        checklist.updated_at = datetime.now().isoformat()
        return True

    def remove_item(
        self,
        checklist_id: str,
        item_id: str,
    ) -> bool:
        """Remove item from checklist."""
        checklist = self.checklists.get(checklist_id)
        if not checklist:
            return False

        for idx, item in enumerate(checklist.items):
            if item.item_id == item_id:
                checklist.items.pop(idx)
                checklist.updated_at = datetime.now().isoformat()
                return True

        return False

    def get_incomplete_required(self, checklist_id: str) -> List[ChecklistItem]:
        """Get incomplete required items."""
        checklist = self.checklists.get(checklist_id)
        if not checklist:
            return []

        return [
            item for item in checklist.items
            if item.required and item.status != "completed"
        ]

    def save_checklist(self, checklist_id: str, path: str) -> bool:
        """Save checklist to file."""
        checklist = self.checklists.get(checklist_id)
        if not checklist:
            return False

        with open(path, "w") as f:
            json.dump(checklist.to_dict(), f, indent=2)

        return True

    def load_checklist(self, path: str) -> Optional[Checklist]:
        """Load checklist from file."""
        try:
            with open(path, "r") as f:
                data = json.load(f)
            checklist = Checklist.from_dict(data)
            self.checklists[checklist.checklist_id] = checklist
            return checklist
        except (json.JSONDecodeError, KeyError):
            return None

    def create_from_template(
        self,
        name: str,
        template_name: str,
    ) -> Optional[Checklist]:
        """
        Create checklist from template.

        Args:
            name: Checklist name
            template_name: Template name

        Returns:
            Created Checklist or None
        """
        templates = {
            "scene_production": SCENE_PRODUCTION_CHECKLIST,
        }

        if template_name not in templates:
            return None

        return self.create_checklist(name, templates[template_name])

    def get_statistics(self) -> Dict[str, Any]:
        """Get manager statistics."""
        return {
            "total_checklists": len(self.checklists),
            "completed_checklists": sum(
                1 for c in self.checklists.values() if c.is_complete
            ),
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "ChecklistStatus",
    # Data classes
    "ChecklistItem",
    "Checklist",
    # Constants
    "SCENE_PRODUCTION_CHECKLIST",
    # Classes
    "ChecklistManager",
]
