"""
Tests for workflow module.

Tests run WITHOUT Blender (bpy) by testing only non-Blender-dependent code paths.
"""

import pytest
import tempfile
import os
import json


class TestApprovalStatus:
    """Tests for ApprovalStatus enum."""

    def test_status_values(self):
        """Test ApprovalStatus enum values."""
        from lib.review.workflow import ApprovalStatus

        assert ApprovalStatus.PENDING.value == "pending"
        assert ApprovalStatus.IN_REVIEW.value == "in_review"
        assert ApprovalStatus.APPROVED.value == "approved"
        assert ApprovalStatus.REJECTED.value == "rejected"
        assert ApprovalStatus.REVISION.value == "revision"
        assert ApprovalStatus.ARCHIVED.value == "archived"


class TestApprovalRecord:
    """Tests for ApprovalRecord dataclass."""

    def test_record_creation(self):
        """Test creating an ApprovalRecord."""
        from lib.review.workflow import ApprovalRecord

        record = ApprovalRecord(
            version_id="ver_001",
            scene_name="Test Scene",
            status="pending",
            created_by="bret",
        )

        assert record.version_id == "ver_001"
        assert record.scene_name == "Test Scene"
        assert record.status == "pending"
        assert record.created_by == "bret"

    def test_record_defaults(self):
        """Test ApprovalRecord default values."""
        from lib.review.workflow import ApprovalRecord

        record = ApprovalRecord()
        assert record.version_id == ""
        assert record.status == "pending"
        assert record.review_history == []
        assert record.artifacts == []

    def test_record_to_dict(self):
        """Test ApprovalRecord serialization."""
        from lib.review.workflow import ApprovalRecord

        record = ApprovalRecord(
            version_id="ver_001",
            scene_name="Test",
            status="approved",
            notes="Looks good",
        )
        data = record.to_dict()

        assert data["version_id"] == "ver_001"
        assert data["scene_name"] == "Test"
        assert data["status"] == "approved"
        assert data["notes"] == "Looks good"

    def test_record_from_dict(self):
        """Test ApprovalRecord deserialization."""
        from lib.review.workflow import ApprovalRecord

        data = {
            "version_id": "ver_001",
            "scene_name": "Test Scene",
            "status": "in_review",
            "created_by": "artist",
            "review_history": [{"action": "submitted"}],
        }
        record = ApprovalRecord.from_dict(data)

        assert record.version_id == "ver_001"
        assert record.status == "in_review"
        assert len(record.review_history) == 1


class TestApprovalWorkflow:
    """Tests for ApprovalWorkflow class."""

    def test_workflow_creation(self):
        """Test creating an ApprovalWorkflow."""
        from lib.review.workflow import ApprovalWorkflow

        workflow = ApprovalWorkflow()
        assert workflow is not None
        assert len(workflow.versions) == 0

    def test_create_version(self):
        """Test creating a version."""
        from lib.review.workflow import ApprovalWorkflow

        workflow = ApprovalWorkflow()
        version = workflow.create_version(
            scene_name="Test Scene",
            created_by="bret",
            notes="Initial version",
        )

        assert version.scene_name == "Test Scene"
        assert version.created_by == "bret"
        assert version.status == "pending"
        assert version.version_id.startswith("ver_")
        assert version.version_id in workflow.versions

    def test_create_version_with_artifacts(self):
        """Test creating version with artifacts."""
        from lib.review.workflow import ApprovalWorkflow

        workflow = ApprovalWorkflow()
        version = workflow.create_version(
            scene_name="Test",
            created_by="bret",
            artifacts=["render_v1.png", "scene_v1.blend"],
        )

        assert len(version.artifacts) == 2
        assert "render_v1.png" in version.artifacts

    def test_get_version(self):
        """Test getting a version."""
        from lib.review.workflow import ApprovalWorkflow

        workflow = ApprovalWorkflow()
        created = workflow.create_version("Test", "bret")
        retrieved = workflow.get_version(created.version_id)

        assert retrieved is created

    def test_get_nonexistent_version(self):
        """Test getting nonexistent version."""
        from lib.review.workflow import ApprovalWorkflow

        workflow = ApprovalWorkflow()
        result = workflow.get_version("nonexistent")
        assert result is None

    def test_submit_for_review(self):
        """Test submitting for review."""
        from lib.review.workflow import ApprovalWorkflow

        workflow = ApprovalWorkflow()
        version = workflow.create_version("Test", "bret")

        result = workflow.submit_for_review(
            version.version_id,
            validation_report_id="val_001",
            notes="Ready for review",
        )

        assert result is True
        assert version.status == "in_review"
        assert version.validation_report_id == "val_001"
        assert len(version.review_history) == 1
        assert version.review_history[0]["action"] == "submitted"

    def test_submit_nonexistent_for_review(self):
        """Test submitting nonexistent version."""
        from lib.review.workflow import ApprovalWorkflow

        workflow = ApprovalWorkflow()
        result = workflow.submit_for_review("nonexistent", "val_001")

        assert result is False

    def test_submit_non_pending_for_review(self):
        """Test submitting non-pending version."""
        from lib.review.workflow import ApprovalWorkflow

        workflow = ApprovalWorkflow()
        version = workflow.create_version("Test", "bret")
        version.status = "approved"

        result = workflow.submit_for_review(version.version_id, "val_001")
        assert result is False

    def test_approve(self):
        """Test approving a version."""
        from lib.review.workflow import ApprovalWorkflow

        workflow = ApprovalWorkflow()
        version = workflow.create_version("Test", "bret")
        workflow.submit_for_review(version.version_id)

        result = workflow.approve(
            version.version_id,
            reviewer="lead_artist",
            notes="Great work!",
        )

        assert result is True
        assert version.status == "approved"
        assert len(version.review_history) == 2
        assert version.review_history[1]["action"] == "approved"
        assert version.review_history[1]["reviewer"] == "lead_artist"

    def test_approve_non_in_review(self):
        """Test approving version not in review."""
        from lib.review.workflow import ApprovalWorkflow

        workflow = ApprovalWorkflow()
        version = workflow.create_version("Test", "bret")
        # Not submitted, so status is "pending"

        result = workflow.approve(version.version_id, "reviewer")
        assert result is False

    def test_reject(self):
        """Test rejecting a version."""
        from lib.review.workflow import ApprovalWorkflow

        workflow = ApprovalWorkflow()
        version = workflow.create_version("Test", "bret")
        workflow.submit_for_review(version.version_id)

        result = workflow.reject(
            version.version_id,
            reviewer="lead",
            reason="Scale is wrong",
        )

        assert result is True
        assert version.status == "rejected"
        assert version.review_history[-1]["reason"] == "Scale is wrong"

    def test_request_revision(self):
        """Test requesting revision."""
        from lib.review.workflow import ApprovalWorkflow

        workflow = ApprovalWorkflow()
        version = workflow.create_version("Test", "bret")
        workflow.submit_for_review(version.version_id)

        result = workflow.request_revision(
            version.version_id,
            reviewer="lead",
            feedback="Fix the lighting",
        )

        assert result is True
        assert version.status == "revision"
        assert version.review_history[-1]["feedback"] == "Fix the lighting"

    def test_request_revision_from_rejected(self):
        """Test requesting revision from rejected state."""
        from lib.review.workflow import ApprovalWorkflow

        workflow = ApprovalWorkflow()
        version = workflow.create_version("Test", "bret")
        workflow.submit_for_review(version.version_id)
        workflow.reject(version.version_id, "reviewer", "bad")

        result = workflow.request_revision(
            version.version_id,
            reviewer="reviewer",
            feedback="Try again",
        )

        assert result is True
        assert version.status == "revision"

    def test_archive(self):
        """Test archiving a version."""
        from lib.review.workflow import ApprovalWorkflow

        workflow = ApprovalWorkflow()
        version = workflow.create_version("Test", "bret")

        result = workflow.archive(version.version_id)

        assert result is True
        assert version.status == "archived"

    def test_get_pending(self):
        """Test getting pending versions."""
        from lib.review.workflow import ApprovalWorkflow

        workflow = ApprovalWorkflow()

        v1 = workflow.create_version("Scene A", "bret")
        v2 = workflow.create_version("Scene B", "bret")
        workflow.submit_for_review(v2.version_id)
        v3 = workflow.create_version("Scene C", "bret")
        v3.status = "approved"

        pending = workflow.get_pending()

        assert len(pending) == 2
        pending_ids = [v.version_id for v in pending]
        assert v1.version_id in pending_ids
        assert v2.version_id in pending_ids
        assert v3.version_id not in pending_ids

    def test_get_approved(self):
        """Test getting approved versions."""
        from lib.review.workflow import ApprovalWorkflow

        workflow = ApprovalWorkflow()

        v1 = workflow.create_version("Scene A", "bret")
        v2 = workflow.create_version("Scene B", "bret")
        workflow.submit_for_review(v2.version_id)
        workflow.approve(v2.version_id, "reviewer")

        approved = workflow.get_approved()

        assert len(approved) == 1
        assert approved[0].version_id == v2.version_id

    def test_get_by_scene(self):
        """Test getting versions by scene."""
        from lib.review.workflow import ApprovalWorkflow

        workflow = ApprovalWorkflow()

        v1 = workflow.create_version("Scene A", "bret")
        v2 = workflow.create_version("Scene A", "bret")
        v3 = workflow.create_version("Scene B", "bret")

        versions = workflow.get_by_scene("Scene A")

        assert len(versions) == 2
        assert v1.version_id in [v.version_id for v in versions]
        assert v2.version_id in [v.version_id for v in versions]

    def test_get_latest_version(self):
        """Test getting latest version for scene."""
        from lib.review.workflow import ApprovalWorkflow

        workflow = ApprovalWorkflow()

        workflow.create_version("Scene A", "bret")
        v2 = workflow.create_version("Scene A", "bret")
        workflow.create_version("Scene B", "bret")

        latest = workflow.get_latest_version("Scene A")

        assert latest.version_id == v2.version_id

    def test_get_latest_version_no_versions(self):
        """Test getting latest version when none exist."""
        from lib.review.workflow import ApprovalWorkflow

        workflow = ApprovalWorkflow()
        result = workflow.get_latest_version("Nonexistent Scene")

        assert result is None

    def test_get_version_history(self):
        """Test getting version history."""
        from lib.review.workflow import ApprovalWorkflow

        workflow = ApprovalWorkflow()

        workflow.create_version("Scene A", "artist1", notes="v1")
        workflow.create_version("Scene A", "artist2", notes="v2")
        workflow.create_version("Scene B", "artist1")

        history = workflow.get_version_history("Scene A")

        assert len(history) == 2
        assert history[0]["notes"] == "v1"
        assert history[1]["notes"] == "v2"

    def test_get_statistics(self):
        """Test getting workflow statistics."""
        from lib.review.workflow import ApprovalWorkflow

        workflow = ApprovalWorkflow()

        v1 = workflow.create_version("Scene A", "bret")
        v2 = workflow.create_version("Scene A", "bret")
        workflow.submit_for_review(v2.version_id)
        workflow.approve(v2.version_id, "reviewer")
        v3 = workflow.create_version("Scene B", "bret")
        v3.status = "rejected"

        stats = workflow.get_statistics()

        assert stats["total_versions"] == 3
        assert stats["by_status"]["approved"] == 1
        assert stats["by_status"]["rejected"] == 1
        assert stats["unique_scenes"] == 2


class TestApprovalWorkflowPersistence:
    """Tests for ApprovalWorkflow persistence."""

    def test_save_and_load_versions(self):
        """Test saving and loading versions from storage."""
        from lib.review.workflow import ApprovalWorkflow

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create workflow with storage
            workflow1 = ApprovalWorkflow(storage_path=temp_dir)
            version = workflow1.create_version("Test Scene", "bret")
            workflow1.submit_for_review(version.version_id)

            # Create new workflow with same storage
            workflow2 = ApprovalWorkflow(storage_path=temp_dir)

            # Should load the version
            assert len(workflow2.versions) == 1
            loaded = workflow2.get_version(version.version_id)
            assert loaded is not None
            assert loaded.scene_name == "Test Scene"
            assert loaded.status == "in_review"

    def test_version_saved_on_status_change(self):
        """Test that version is saved on status change."""
        from lib.review.workflow import ApprovalWorkflow

        with tempfile.TemporaryDirectory() as temp_dir:
            workflow = ApprovalWorkflow(storage_path=temp_dir)
            version = workflow.create_version("Test", "bret")
            workflow.submit_for_review(version.version_id)
            workflow.approve(version.version_id, "reviewer")

            # Check file exists
            version_file = os.path.join(temp_dir, f"{version.version_id}.json")
            assert os.path.exists(version_file)

            with open(version_file) as f:
                data = json.load(f)
                assert data["status"] == "approved"


class TestWorkflowWithoutStorage:
    """Tests for workflow without storage path."""

    def test_workflow_no_storage(self):
        """Test workflow works without storage path."""
        from lib.review.workflow import ApprovalWorkflow

        workflow = ApprovalWorkflow()
        version = workflow.create_version("Test", "bret")
        workflow.submit_for_review(version.version_id)

        # Should work fine
        assert version.status == "in_review"
