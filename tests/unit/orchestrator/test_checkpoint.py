"""
Tests for Orchestrator Checkpoint System

Tests checkpoint save/restore functionality.
"""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch
from lib.orchestrator.checkpoint import (
    Checkpoint,
    CheckpointManager,
    CheckpointError,
    GenerationStage,
    CheckpointContext,
    resume_from_checkpoint,
    auto_checkpoint,
)


class TestCheckpoint:
    """Tests for Checkpoint dataclass."""

    def test_create_default(self):
        """Test creating Checkpoint with defaults."""
        cp = Checkpoint()
        assert cp.checkpoint_id == ""
        assert cp.session_id == ""
        assert cp.stage == "initialized"
        assert cp.status == "active"
        assert cp.timestamp == ""
        assert cp.scene_outline is None
        assert cp.asset_selections == []
        assert cp.generation_state == {}
        assert cp.progress == {}
        assert cp.errors == []
        assert cp.metadata == {}

    def test_create_with_values(self):
        """Test creating Checkpoint with values."""
        cp = Checkpoint(
            checkpoint_id="cp_001",
            session_id="session_001",
            stage="asset_selection",
            status="active",
            timestamp="2024-01-01T00:00:00",
            scene_outline={"name": "test"},
            asset_selections=[{"asset": "car"}],
            generation_state={"progress": 50},
            progress={"percent": 50},
            errors=["warning1"],
            metadata={"key": "value"},
        )
        assert cp.checkpoint_id == "cp_001"
        assert cp.session_id == "session_001"
        assert cp.stage == "asset_selection"
        assert cp.status == "active"
        assert cp.timestamp == "2024-01-01T00:00:00"
        assert cp.scene_outline == {"name": "test"}
        assert cp.asset_selections == [{"asset": "car"}]
        assert cp.generation_state == {"progress": 50}
        assert cp.progress == {"percent": 50}
        assert cp.errors == ["warning1"]
        assert cp.metadata == {"key": "value"}

    def test_to_dict(self):
        """Test Checkpoint serialization."""
        cp = Checkpoint(
            checkpoint_id="test_id",
            session_id="test_session",
            stage="complete",
            status="completed",
        )
        result = cp.to_dict()
        assert result["checkpoint_id"] == "test_id"
        assert result["session_id"] == "test_session"
        assert result["stage"] == "complete"
        assert result["status"] == "completed"

    def test_from_dict(self):
        """Test Checkpoint deserialization."""
        data = {
            "checkpoint_id": "loaded_id",
            "session_id": "loaded_session",
            "stage": "rendering",
            "status": "active",
            "timestamp": "2024-01-01T12:00:00",
            "scene_outline": {"scene": "test"},
            "asset_selections": [{"id": "a1"}],
            "generation_state": {"step": 3},
            "progress": {"percent": 75},
            "errors": ["err1"],
            "metadata": {"source": "test"},
        }
        cp = Checkpoint.from_dict(data)
        assert cp.checkpoint_id == "loaded_id"
        assert cp.session_id == "loaded_session"
        assert cp.stage == "rendering"
        assert cp.status == "active"
        assert cp.timestamp == "2024-01-01T12:00:00"
        assert cp.scene_outline == {"scene": "test"}
        assert cp.asset_selections == [{"id": "a1"}]
        assert cp.generation_state == {"step": 3}
        assert cp.progress == {"percent": 75}
        assert cp.errors == ["err1"]
        assert cp.metadata == {"source": "test"}

    def test_roundtrip(self):
        """Test to_dict -> from_dict roundtrip."""
        original = Checkpoint(
            checkpoint_id="roundtrip",
            session_id="session",
            stage="testing",
            scene_outline={"type": "urban"},
            asset_selections=[{"a": 1}, {"b": 2}],
        )
        restored = Checkpoint.from_dict(original.to_dict())
        assert restored.checkpoint_id == original.checkpoint_id
        assert restored.session_id == original.session_id
        assert restored.stage == original.stage
        assert restored.scene_outline == original.scene_outline
        assert restored.asset_selections == original.asset_selections


class TestGenerationStage:
    """Tests for GenerationStage constants."""

    def test_stage_constants(self):
        """Test that all stage constants are defined."""
        assert GenerationStage.INITIALIZED == "initialized"
        assert GenerationStage.PARSING == "parsing"
        assert GenerationStage.REQUIREMENT_RESOLUTION == "requirement_resolution"
        assert GenerationStage.ASSET_SELECTION == "asset_selection"
        assert GenerationStage.PLACEMENT == "placement"
        assert GenerationStage.GEOMETRY_GENERATION == "geometry_generation"
        assert GenerationStage.MATERIAL_APPLICATION == "material_application"
        assert GenerationStage.LIGHTING_SETUP == "lighting_setup"
        assert GenerationStage.CAMERA_SETUP == "camera_setup"
        assert GenerationStage.POST_PROCESSING == "post_processing"
        assert GenerationStage.VALIDATION == "validation"
        assert GenerationStage.COMPLETED == "completed"
        assert GenerationStage.FAILED == "failed"


class TestCheckpointManager:
    """Tests for CheckpointManager class."""

    def test_init(self):
        """Test CheckpointManager initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(checkpoint_dir=tmpdir)
            assert str(manager.checkpoint_dir) == tmpdir
            assert manager._current_session.startswith("session_")

    def test_create_checkpoint(self):
        """Test creating a checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(checkpoint_dir=tmpdir)
            cp = manager.create_checkpoint(
                scene_outline={"name": "test"},
                stage=GenerationStage.INITIALIZED,
            )
            assert cp.checkpoint_id.startswith("cp_")
            assert cp.session_id == manager._current_session
            assert cp.stage == GenerationStage.INITIALIZED
            assert cp.status == "active"
            assert cp.timestamp != ""

    def test_load_checkpoint(self):
        """Test loading a checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(checkpoint_dir=tmpdir)
            created = manager.create_checkpoint(
                scene_outline={"scene": "test"},
                stage="test_stage",
                generation_state={"key": "value"},
            )
            loaded = manager.load_checkpoint(created.checkpoint_id)
            assert loaded is not None
            assert loaded.checkpoint_id == created.checkpoint_id
            assert loaded.stage == "test_stage"
            assert loaded.generation_state == {"key": "value"}

    def test_load_nonexistent_checkpoint(self):
        """Test loading a nonexistent checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(checkpoint_dir=tmpdir)
            loaded = manager.load_checkpoint("nonexistent_id")
            assert loaded is None

    def test_delete_checkpoint(self):
        """Test deleting a checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(checkpoint_dir=tmpdir)
            cp = manager.create_checkpoint()
            assert manager.delete_checkpoint(cp.checkpoint_id) is True
            loaded = manager.load_checkpoint(cp.checkpoint_id)
            assert loaded is None

    def test_delete_nonexistent_checkpoint(self):
        """Test deleting a nonexistent checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(checkpoint_dir=tmpdir)
            assert manager.delete_checkpoint("nonexistent") is False

    def test_list_checkpoints(self):
        """Test listing checkpoints."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(checkpoint_dir=tmpdir)
            manager.create_checkpoint(stage="stage_1")
            manager.create_checkpoint(stage="stage_2")
            checkpoints = manager.list_checkpoints()
            assert len(checkpoints) >= 2

    def test_list_checkpoints_with_filter(self):
        """Test listing checkpoints with filters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(checkpoint_dir=tmpdir)
            manager.create_checkpoint(stage="stage_1")
            manager.create_checkpoint(stage="stage_2")
            checkpoints = manager.list_checkpoints(stage="stage_1")
            assert len(checkpoints) == 1
            assert checkpoints[0]["stage"] == "stage_1"

    def test_get_latest_checkpoint(self):
        """Test getting latest checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(checkpoint_dir=tmpdir)
            manager.create_checkpoint(stage="first")
            manager.create_checkpoint(stage="second")
            latest = manager.get_latest_checkpoint()
            assert latest is not None
            assert latest.stage == "second"

    def test_update_checkpoint(self):
        """Test updating a checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(checkpoint_dir=tmpdir)
            cp = manager.create_checkpoint(stage="initial")
            updated = manager.update_checkpoint(
                cp.checkpoint_id,
                stage="updated",
                progress={"percent": 50},
            )
            assert updated is not None
            assert updated.stage == "updated"
            assert updated.progress == {"percent": 50}

    def test_update_nonexistent_checkpoint(self):
        """Test updating a nonexistent checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(checkpoint_dir=tmpdir)
            updated = manager.update_checkpoint("nonexistent", stage="test")
            assert updated is None


class TestCheckpointContext:
    """Tests for CheckpointContext context manager."""

    def test_context_success(self):
        """Test context manager on success."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(checkpoint_dir=tmpdir)
            with CheckpointContext(manager, stage="test") as ctx:
                assert ctx.checkpoint is not None
                assert ctx.checkpoint.stage == "test"
            # After context, checkpoint should be completed
            loaded = manager.load_checkpoint(ctx.checkpoint.checkpoint_id)
            assert loaded.status == "completed"

    def test_context_with_error(self):
        """Test context manager on error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(checkpoint_dir=tmpdir)
            with pytest.raises(ValueError):
                with CheckpointContext(manager, stage="test") as ctx:
                    raise ValueError("test error")
            # After context with error, checkpoint should be failed
            loaded = manager.load_checkpoint(ctx.checkpoint.checkpoint_id)
            assert loaded.status == "failed"
            assert loaded.stage == "failed"
            assert "test error" in loaded.errors

    def test_context_update(self):
        """Test updating checkpoint within context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(checkpoint_dir=tmpdir)
            with CheckpointContext(manager, stage="test") as ctx:
                ctx.update(progress={"percent": 50})
            loaded = manager.load_checkpoint(ctx.checkpoint.checkpoint_id)
            assert loaded.progress == {"percent": 50}


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_resume_from_checkpoint(self):
        """Test resume_from_checkpoint function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(checkpoint_dir=tmpdir)
            cp = manager.create_checkpoint(stage="test_stage")
            loaded = resume_from_checkpoint(cp.checkpoint_id, checkpoint_dir=tmpdir)
            assert loaded is not None
            assert loaded.stage == "test_stage"

    def test_auto_checkpoint(self):
        """Test auto_checkpoint function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(checkpoint_dir=tmpdir)
            cp = auto_checkpoint(
                manager,
                stage="asset_selection",
                scene_outline={"name": "test"},
                state={"progress": 25},
            )
            assert cp.stage == "asset_selection"
            assert cp.generation_state == {"progress": 25}
            assert cp.metadata.get("auto") is True


class TestCheckpointRoundTrip:
    """Tests for checkpoint save/load round trips."""

    def test_complex_data_round_trip(self):
        """Test round trip with complex data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(checkpoint_dir=tmpdir)
            cp = manager.create_checkpoint(
                scene_outline={
                    "assets": [{"id": "a1"}, {"id": "a2"}],
                    "settings": {"quality": "high", "samples": 128},
                    "nested": {"deep": {"value": 42}},
                },
                stage="advanced",
            )
            loaded = manager.load_checkpoint(cp.checkpoint_id)
            assert loaded.scene_outline["assets"][0]["id"] == "a1"
            assert loaded.scene_outline["settings"]["samples"] == 128
            assert loaded.scene_outline["nested"]["deep"]["value"] == 42

    def test_unicode_data_round_trip(self):
        """Test round trip with unicode data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(checkpoint_dir=tmpdir)
            cp = manager.create_checkpoint(
                scene_outline={
                    "name": "Test Scene - 日本語",
                    "description": "A test with émojis 🎬",
                },
                stage="test",
            )
            loaded = manager.load_checkpoint(cp.checkpoint_id)
            assert loaded.scene_outline["name"] == "Test Scene - 日本語"
            assert "🎬" in loaded.scene_outline["description"]
