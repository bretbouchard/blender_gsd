"""
Tests for checklists module.

Tests run WITHOUT Blender (bpy) by testing only non-Blender-dependent code paths.
"""

import pytest
import json
import tempfile
import os
from datetime import datetime


class TestChecklistItem:
    """Tests for ChecklistItem dataclass."""

    def test_checklist_item_creation(self):
        """Test creating a ChecklistItem."""
        from lib.review.checklists import ChecklistItem

        item = ChecklistItem(
            item_id="test_001",
            name="Test Item",
            description="Test description",
        )
        assert item.item_id == "test_001"
        assert item.name == "Test Item"
        assert item.description == "Test description"

    def test_checklist_item_defaults(self):
        """Test ChecklistItem default values."""
        from lib.review.checklists import ChecklistItem

        item = ChecklistItem()
        assert item.item_id == ""
        assert item.name == ""
        assert item.status == "pending"
        assert item.required is True
        assert item.auto_check is False

    def test_checklist_item_to_dict(self):
        """Test ChecklistItem serialization."""
        from lib.review.checklists import ChecklistItem

        item = ChecklistItem(
            item_id="test_001",
            name="Test Item",
            status="completed",
        )
        data = item.to_dict()

        assert isinstance(data, dict)
        assert data["item_id"] == "test_001"
        assert data["name"] == "Test Item"
        assert data["status"] == "completed"

    def test_checklist_item_from_dict(self):
        """Test ChecklistItem deserialization."""
        from lib.review.checklists import ChecklistItem

        data = {
            "item_id": "test_001",
            "name": "Test Item",
            "description": "Test desc",
            "status": "completed",
            "required": False,
        }
        item = ChecklistItem.from_dict(data)

        assert item.item_id == "test_001"
        assert item.name == "Test Item"
        assert item.status == "completed"
        assert item.required is False


class TestChecklist:
    """Tests for Checklist dataclass."""

    def test_checklist_creation(self):
        """Test creating a Checklist."""
        from lib.review.checklists import Checklist, ChecklistItem

        items = [
            ChecklistItem(item_id="item_1", name="First"),
            ChecklistItem(item_id="item_2", name="Second"),
        ]

        checklist = Checklist(
            checklist_id="check_001",
            name="Test Checklist",
            items=items,
        )

        assert checklist.checklist_id == "check_001"
        assert checklist.name == "Test Checklist"
        assert len(checklist.items) == 2

    def test_checklist_total_items(self):
        """Test total_items property."""
        from lib.review.checklists import Checklist, ChecklistItem

        checklist = Checklist(items=[
            ChecklistItem(item_id="1"),
            ChecklistItem(item_id="2"),
            ChecklistItem(item_id="3"),
        ])

        assert checklist.total_items == 3

    def test_checklist_completed_count(self):
        """Test completed_count property."""
        from lib.review.checklists import Checklist, ChecklistItem

        checklist = Checklist(items=[
            ChecklistItem(item_id="1", status="completed"),
            ChecklistItem(item_id="2", status="pending"),
            ChecklistItem(item_id="3", status="completed"),
        ])

        assert checklist.completed_count == 2

    def test_checklist_completion_percentage(self):
        """Test completion_percentage property."""
        from lib.review.checklists import Checklist, ChecklistItem

        checklist = Checklist(items=[
            ChecklistItem(item_id="1", status="completed"),
            ChecklistItem(item_id="2", status="pending"),
        ])

        assert checklist.completion_percentage == 50.0

    def test_checklist_empty_completion_percentage(self):
        """Test completion_percentage with empty checklist."""
        from lib.review.checklists import Checklist

        checklist = Checklist(items=[])
        assert checklist.completion_percentage == 0.0

    def test_checklist_required_properties(self):
        """Test required item properties."""
        from lib.review.checklists import Checklist, ChecklistItem

        checklist = Checklist(items=[
            ChecklistItem(item_id="1", required=True, status="completed"),
            ChecklistItem(item_id="2", required=True, status="pending"),
            ChecklistItem(item_id="3", required=False, status="pending"),
        ])

        assert checklist.required_total == 2
        assert checklist.required_completed == 1

    def test_checklist_is_complete(self):
        """Test is_complete property."""
        from lib.review.checklists import Checklist, ChecklistItem

        # Not complete
        checklist1 = Checklist(items=[
            ChecklistItem(item_id="1", required=True, status="completed"),
            ChecklistItem(item_id="2", required=True, status="pending"),
        ])
        assert checklist1.is_complete is False

        # Complete
        checklist2 = Checklist(items=[
            ChecklistItem(item_id="1", required=True, status="completed"),
            ChecklistItem(item_id="2", required=True, status="completed"),
            ChecklistItem(item_id="3", required=False, status="pending"),
        ])
        assert checklist2.is_complete is True

    def test_checklist_to_dict(self):
        """Test Checklist serialization."""
        from lib.review.checklists import Checklist, ChecklistItem

        checklist = Checklist(
            checklist_id="check_001",
            name="Test",
            items=[ChecklistItem(item_id="1", name="Item")],
        )
        data = checklist.to_dict()

        assert data["checklist_id"] == "check_001"
        assert data["name"] == "Test"
        assert len(data["items"]) == 1

    def test_checklist_from_dict(self):
        """Test Checklist deserialization."""
        from lib.review.checklists import Checklist

        data = {
            "checklist_id": "check_001",
            "name": "Test Checklist",
            "items": [
                {"item_id": "1", "name": "First"},
                {"item_id": "2", "name": "Second"},
            ],
        }
        checklist = Checklist.from_dict(data)

        assert checklist.checklist_id == "check_001"
        assert len(checklist.items) == 2


class TestChecklistManager:
    """Tests for ChecklistManager class."""

    def test_manager_creation(self):
        """Test creating a ChecklistManager."""
        from lib.review.checklists import ChecklistManager

        manager = ChecklistManager()
        assert manager is not None
        assert len(manager.checklists) == 0

    def test_create_checklist(self):
        """Test creating a checklist through manager."""
        from lib.review.checklists import ChecklistManager

        manager = ChecklistManager()
        checklist = manager.create_checklist(
            name="Test Checklist",
            description="Test description",
        )

        assert checklist.name == "Test Checklist"
        assert checklist.checklist_id in manager.checklists

    def test_create_checklist_with_items(self):
        """Test creating checklist with initial items."""
        from lib.review.checklists import ChecklistManager

        manager = ChecklistManager()
        items = [
            {"item_id": "item_1", "name": "First"},
            {"item_id": "item_2", "name": "Second"},
        ]
        checklist = manager.create_checklist(name="Test", items=items)

        assert len(checklist.items) == 2
        assert checklist.items[0].name == "First"

    def test_get_checklist(self):
        """Test getting a checklist by ID."""
        from lib.review.checklists import ChecklistManager

        manager = ChecklistManager()
        created = manager.create_checklist(name="Test")
        retrieved = manager.get_checklist(created.checklist_id)

        assert retrieved is created

    def test_get_nonexistent_checklist(self):
        """Test getting a nonexistent checklist."""
        from lib.review.checklists import ChecklistManager

        manager = ChecklistManager()
        result = manager.get_checklist("nonexistent")
        assert result is None

    def test_check_item(self):
        """Test checking an item."""
        from lib.review.checklists import ChecklistManager

        manager = ChecklistManager()
        checklist = manager.create_checklist(name="Test", items=[
            {"item_id": "item_1", "name": "First"},
        ])

        result = manager.check_item(
            checklist.checklist_id,
            "item_1",
            "completed",
            notes="Done!",
            completed_by="tester",
        )

        assert result is True
        assert checklist.items[0].status == "completed"
        assert checklist.items[0].notes == "Done!"
        assert checklist.items[0].completed_by == "tester"

    def test_check_item_nonexistent_checklist(self):
        """Test checking item in nonexistent checklist."""
        from lib.review.checklists import ChecklistManager

        manager = ChecklistManager()
        result = manager.check_item("nonexistent", "item_1", "completed")
        assert result is False

    def test_check_nonexistent_item(self):
        """Test checking nonexistent item."""
        from lib.review.checklists import ChecklistManager

        manager = ChecklistManager()
        checklist = manager.create_checklist(name="Test")
        result = manager.check_item(checklist.checklist_id, "nonexistent", "completed")
        assert result is False

    def test_add_item(self):
        """Test adding item to checklist."""
        from lib.review.checklists import ChecklistManager, ChecklistItem

        manager = ChecklistManager()
        checklist = manager.create_checklist(name="Test")

        new_item = ChecklistItem(item_id="new", name="New Item")
        result = manager.add_item(checklist.checklist_id, new_item)

        assert result is True
        assert len(checklist.items) == 1

    def test_remove_item(self):
        """Test removing item from checklist."""
        from lib.review.checklists import ChecklistManager

        manager = ChecklistManager()
        checklist = manager.create_checklist(name="Test", items=[
            {"item_id": "item_1", "name": "First"},
            {"item_id": "item_2", "name": "Second"},
        ])

        result = manager.remove_item(checklist.checklist_id, "item_1")
        assert result is True
        assert len(checklist.items) == 1
        assert checklist.items[0].item_id == "item_2"

    def test_get_incomplete_required(self):
        """Test getting incomplete required items."""
        from lib.review.checklists import ChecklistManager, ChecklistItem

        manager = ChecklistManager()
        checklist = manager.create_checklist(name="Test")

        # Add items manually with statuses (since create_checklist doesn't preserve status from dict)
        item1 = ChecklistItem(item_id="1", required=True, status="completed")
        item2 = ChecklistItem(item_id="2", required=True, status="pending")
        item3 = ChecklistItem(item_id="3", required=False, status="pending")
        checklist.items = [item1, item2, item3]

        incomplete = manager.get_incomplete_required(checklist.checklist_id)
        assert len(incomplete) == 1
        assert incomplete[0].item_id == "2"

    def test_save_and_load_checklist(self):
        """Test saving and loading checklist."""
        from lib.review.checklists import ChecklistManager

        manager = ChecklistManager()
        checklist = manager.create_checklist(name="Test", items=[
            {"item_id": "1", "name": "First"},
        ])

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            result = manager.save_checklist(checklist.checklist_id, temp_path)
            assert result is True

            # Create new manager and load
            new_manager = ChecklistManager()
            loaded = new_manager.load_checklist(temp_path)

            assert loaded is not None
            assert loaded.name == "Test"
            assert len(loaded.items) == 1
        finally:
            os.unlink(temp_path)

    def test_create_from_template(self):
        """Test creating from template."""
        from lib.review.checklists import ChecklistManager

        manager = ChecklistManager()
        checklist = manager.create_from_template(
            name="Scene Review",
            template_name="scene_production",
        )

        assert checklist is not None
        assert checklist.name == "Scene Review"
        assert len(checklist.items) > 0

    def test_create_from_invalid_template(self):
        """Test creating from invalid template."""
        from lib.review.checklists import ChecklistManager

        manager = ChecklistManager()
        result = manager.create_from_template(
            name="Test",
            template_name="nonexistent_template",
        )
        assert result is None

    def test_get_statistics(self):
        """Test getting manager statistics."""
        from lib.review.checklists import ChecklistManager, ChecklistItem

        manager = ChecklistManager()

        # Create completed checklist
        checklist1 = manager.create_checklist(name="Checklist 1")
        checklist1.items = [ChecklistItem(item_id="1", required=True, status="completed")]

        # Create incomplete checklist
        checklist2 = manager.create_checklist(name="Checklist 2")
        checklist2.items = [ChecklistItem(item_id="1", required=True, status="pending")]

        stats = manager.get_statistics()
        assert stats["total_checklists"] == 2
        assert stats["completed_checklists"] == 1


class TestChecklistStatus:
    """Tests for ChecklistStatus enum."""

    def test_status_values(self):
        """Test ChecklistStatus enum values."""
        from lib.review.checklists import ChecklistStatus

        assert ChecklistStatus.PENDING.value == "pending"
        assert ChecklistStatus.IN_PROGRESS.value == "in_progress"
        assert ChecklistStatus.COMPLETED.value == "completed"
        assert ChecklistStatus.SKIPPED.value == "skipped"
        assert ChecklistStatus.FAILED.value == "failed"


class TestSceneProductionChecklist:
    """Tests for SCENE_PRODUCTION_CHECKLIST constant."""

    def test_checklist_structure(self):
        """Test scene production checklist structure."""
        from lib.review.checklists import SCENE_PRODUCTION_CHECKLIST

        assert isinstance(SCENE_PRODUCTION_CHECKLIST, list)
        assert len(SCENE_PRODUCTION_CHECKLIST) > 0

        # Check required items exist
        item_ids = [item["item_id"] for item in SCENE_PRODUCTION_CHECKLIST]
        assert "scale_check" in item_ids
        assert "material_assignment" in item_ids
        assert "lighting_setup" in item_ids

    def test_checklist_items_have_required_fields(self):
        """Test that all items have required fields."""
        from lib.review.checklists import SCENE_PRODUCTION_CHECKLIST

        for item in SCENE_PRODUCTION_CHECKLIST:
            assert "item_id" in item
            assert "name" in item
            assert "category" in item
            assert "required" in item
