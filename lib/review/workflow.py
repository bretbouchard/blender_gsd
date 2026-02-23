"""
Approval Workflow

Approval workflow for scene generation review.

Implements REQ-QA-05: Approval Workflow.
Implements REQ-QA-06: Version History.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
from pathlib import Path
from datetime import datetime
import json


class ApprovalStatus(Enum):
    """Approval status."""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION = "revision"
    ARCHIVED = "archived"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ApprovalRecord:
    """
    Approval record for version.

    Attributes:
        version_id: Unique version identifier
        scene_name: Scene name
        status: Current approval status
        created_at: Creation timestamp
        created_by: Creator
        review_history: List of review events
        validation_report_id: Associated validation report
        notes: Additional notes
        artifacts: Associated artifact paths
        metadata: Additional metadata
    """
    version_id: str = ""
    scene_name: str = ""
    status: str = "pending"
    created_at: str = ""
    created_by: str = ""
    review_history: List[Dict[str, Any]] = field(default_factory=list)
    validation_report_id: str = ""
    notes: str = ""
    artifacts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version_id": self.version_id,
            "scene_name": self.scene_name,
            "status": self.status,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "review_history": self.review_history,
            "validation_report_id": self.validation_report_id,
            "notes": self.notes,
            "artifacts": self.artifacts,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ApprovalRecord":
        """Create from dictionary."""
        return cls(
            version_id=data.get("version_id", ""),
            scene_name=data.get("scene_name", ""),
            status=data.get("status", "pending"),
            created_at=data.get("created_at", ""),
            created_by=data.get("created_by", ""),
            review_history=data.get("review_history", []),
            validation_report_id=data.get("validation_report_id", ""),
            notes=data.get("notes", ""),
            artifacts=data.get("artifacts", []),
            metadata=data.get("metadata", {}),
        )


# =============================================================================
# APPROVAL WORKFLOW CLASS
# =============================================================================

class ApprovalWorkflow:
    """
    Manages approval workflow for scenes.

    Tracks versions, reviews, and approval status.

    Usage:
        workflow = ApprovalWorkflow()
        version = workflow.create_version("scene_001", "bret")
        workflow.submit_for_review(version.version_id, "validation_report_001")
        workflow.approve(version.version_id, "reviewer", "Looks good!")
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize workflow.

        Args:
            storage_path: Path for version storage
        """
        self.versions: Dict[str, ApprovalRecord] = {}
        self.storage_path = Path(storage_path) if storage_path else None
        self._version_counter = 0

        if self.storage_path and self.storage_path.exists():
            self._load_versions()

    def _load_versions(self) -> None:
        """Load versions from storage."""
        if not self.storage_path:
            return

        for version_file in self.storage_path.glob("*.json"):
            try:
                with open(version_file, "r") as f:
                    data = json.load(f)
                version = ApprovalRecord.from_dict(data)
                self.versions[version.version_id] = version
            except (json.JSONDecodeError, KeyError):
                continue

    def _save_version(self, version: ApprovalRecord) -> bool:
        """Save version to storage."""
        if not self.storage_path:
            return True

        self.storage_path.mkdir(parents=True, exist_ok=True)
        version_file = self.storage_path / f"{version.version_id}.json"

        try:
            with open(version_file, "w") as f:
                json.dump(version.to_dict(), f, indent=2)
            return True
        except IOError:
            return False

    def create_version(
        self,
        scene_name: str,
        created_by: str,
        artifacts: Optional[List[str]] = None,
        notes: str = "",
    ) -> ApprovalRecord:
        """
        Create new version.

        Args:
            scene_name: Scene name
            created_by: Creator name
            artifacts: Associated artifacts
            notes: Version notes

        Returns:
            Created ApprovalRecord
        """
        self._version_counter += 1
        version_id = f"ver_{self._version_counter:06d}"

        version = ApprovalRecord(
            version_id=version_id,
            scene_name=scene_name,
            status="pending",
            created_at=datetime.now().isoformat(),
            created_by=created_by,
            notes=notes,
            artifacts=artifacts or [],
        )

        self.versions[version_id] = version
        self._save_version(version)
        return version

    def get_version(self, version_id: str) -> Optional[ApprovalRecord]:
        """Get version by ID."""
        return self.versions.get(version_id)

    def submit_for_review(
        self,
        version_id: str,
        validation_report_id: str = "",
        notes: str = "",
    ) -> bool:
        """
        Submit version for review.

        Args:
            version_id: Version ID
            validation_report_id: Associated validation report
            notes: Submission notes

        Returns:
            Success status
        """
        version = self.versions.get(version_id)
        if not version:
            return False

        if version.status != "pending":
            return False

        version.status = "in_review"
        version.validation_report_id = validation_report_id

        version.review_history.append({
            "action": "submitted",
            "timestamp": datetime.now().isoformat(),
            "notes": notes,
        })

        self._save_version(version)
        return True

    def approve(
        self,
        version_id: str,
        reviewer: str,
        notes: str = "",
    ) -> bool:
        """
        Approve version.

        Args:
            version_id: Version ID
            reviewer: Reviewer name
            notes: Approval notes

        Returns:
            Success status
        """
        version = self.versions.get(version_id)
        if not version:
            return False

        if version.status != "in_review":
            return False

        version.status = "approved"

        version.review_history.append({
            "action": "approved",
            "timestamp": datetime.now().isoformat(),
            "reviewer": reviewer,
            "notes": notes,
        })

        self._save_version(version)
        return True

    def reject(
        self,
        version_id: str,
        reviewer: str,
        reason: str,
    ) -> bool:
        """
        Reject version.

        Args:
            version_id: Version ID
            reviewer: Reviewer name
            reason: Rejection reason

        Returns:
            Success status
        """
        version = self.versions.get(version_id)
        if not version:
            return False

        if version.status != "in_review":
            return False

        version.status = "rejected"

        version.review_history.append({
            "action": "rejected",
            "timestamp": datetime.now().isoformat(),
            "reviewer": reviewer,
            "reason": reason,
        })

        self._save_version(version)
        return True

    def request_revision(
        self,
        version_id: str,
        reviewer: str,
        feedback: str,
    ) -> bool:
        """
        Request revision.

        Args:
            version_id: Version ID
            reviewer: Reviewer name
            feedback: Revision feedback

        Returns:
            Success status
        """
        version = self.versions.get(version_id)
        if not version:
            return False

        if version.status not in ("in_review", "rejected"):
            return False

        version.status = "revision"

        version.review_history.append({
            "action": "revision_requested",
            "timestamp": datetime.now().isoformat(),
            "reviewer": reviewer,
            "feedback": feedback,
        })

        self._save_version(version)
        return True

    def archive(self, version_id: str) -> bool:
        """
        Archive version.

        Args:
            version_id: Version ID

        Returns:
            Success status
        """
        version = self.versions.get(version_id)
        if not version:
            return False

        version.status = "archived"

        version.review_history.append({
            "action": "archived",
            "timestamp": datetime.now().isoformat(),
        })

        self._save_version(version)
        return True

    def get_pending(self) -> List[ApprovalRecord]:
        """Get all pending versions."""
        return [
            v for v in self.versions.values()
            if v.status in ("pending", "in_review", "revision")
        ]

    def get_approved(self) -> List[ApprovalRecord]:
        """Get all approved versions."""
        return [
            v for v in self.versions.values()
            if v.status == "approved"
        ]

    def get_by_scene(self, scene_name: str) -> List[ApprovalRecord]:
        """Get all versions for scene."""
        return [
            v for v in self.versions.values()
            if v.scene_name == scene_name
        ]

    def get_latest_version(self, scene_name: str) -> Optional[ApprovalRecord]:
        """Get latest version for scene."""
        versions = self.get_by_scene(scene_name)
        if not versions:
            return None

        return max(versions, key=lambda v: v.created_at)

    def get_version_history(self, scene_name: str) -> List[Dict[str, Any]]:
        """
        Get version history for scene.

        Args:
            scene_name: Scene name

        Returns:
            List of version history entries
        """
        versions = self.get_by_scene(scene_name)
        history = []

        for version in sorted(versions, key=lambda v: v.created_at):
            history.append({
                "version_id": version.version_id,
                "status": version.status,
                "created_at": version.created_at,
                "created_by": version.created_by,
                "review_count": len(version.review_history),
                "notes": version.notes,
            })

        return history

    def get_statistics(self) -> Dict[str, Any]:
        """Get workflow statistics."""
        stats = {
            "total_versions": len(self.versions),
            "by_status": {},
            "unique_scenes": len(set(v.scene_name for v in self.versions.values())),
        }

        for version in self.versions.values():
            status = version.status
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

        return stats


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "ApprovalStatus",
    # Data classes
    "ApprovalRecord",
    # Classes
    "ApprovalWorkflow",
]
