"""
Tests for Wardrobe System - Costume Manager

Tests for costume_manager.py.
"""

import pytest

from lib.character.wardrobe_types import (
    Costume,
    CostumePiece,
    CostumeAssignment,
    CostumeChange,
    WardrobeRegistry,
)
from lib.character.costume_manager import (
    CostumeManager,
    CostumeManagerError,
    CostumeNotFoundError,
    DuplicateCostumeError,
    InvalidAssignmentError,
)


@pytest.fixture
def sample_costume():
    """Create a sample costume for testing."""
    return Costume(
        name="hero_casual",
        character="Hero",
        pieces=[
            CostumePiece(name="T-Shirt", category="top", color="navy", material="cotton"),
            CostumePiece(name="Jeans", category="bottom", color="blue", material="denim"),
        ],
        colors=["navy", "blue"],
    )


@pytest.fixture
def manager():
    """Create a costume manager for testing."""
    return CostumeManager(production_name="Test Production")


class TestCostumeManagerInit:
    """Tests for CostumeManager initialization."""

    def test_init(self):
        """Test basic initialization."""
        manager = CostumeManager()
        assert manager.registry is not None
        assert manager.registry.production_name == ""

    def test_init_with_name(self):
        """Test initialization with production name."""
        manager = CostumeManager(production_name="My Movie")
        assert manager.registry.production_name == "My Movie"


class TestCostumeCRUD:
    """Tests for costume CRUD operations."""

    def test_create_costume(self, manager, sample_costume):
        """Test creating a costume."""
        manager.create_costume(sample_costume)
        assert "hero_casual" in manager.registry.costumes

    def test_create_duplicate_costume(self, manager, sample_costume):
        """Test creating a duplicate costume raises error."""
        manager.create_costume(sample_costume)
        with pytest.raises(DuplicateCostumeError):
            manager.create_costume(sample_costume)

    def test_get_costume(self, manager, sample_costume):
        """Test getting a costume."""
        manager.create_costume(sample_costume)
        retrieved = manager.get_costume("hero_casual")
        assert retrieved is not None
        assert retrieved.name == "hero_casual"

    def test_get_nonexistent_costume(self, manager):
        """Test getting a nonexistent costume returns None."""
        retrieved = manager.get_costume("nonexistent")
        assert retrieved is None

    def test_update_costume(self, manager, sample_costume):
        """Test updating a costume."""
        manager.create_costume(sample_costume)

        updated = Costume(
            name="hero_casual",
            character="Hero",
            pieces=[
                CostumePiece(name="T-Shirt", category="top", color="red", material="cotton"),
            ],
            colors=["red"],
        )
        manager.update_costume("hero_casual", updated)

        retrieved = manager.get_costume("hero_casual")
        assert retrieved.colors == ["red"]

    def test_update_nonexistent_costume(self, manager):
        """Test updating a nonexistent costume raises error."""
        costume = Costume(
            name="nonexistent",
            character="Hero",
            pieces=[],
        )
        with pytest.raises(CostumeNotFoundError):
            manager.update_costume("nonexistent", costume)

    def test_delete_costume(self, manager, sample_costume):
        """Test deleting a costume."""
        manager.create_costume(sample_costume)
        result = manager.delete_costume("hero_casual")
        assert result is True
        assert "hero_casual" not in manager.registry.costumes

    def test_delete_nonexistent_costume(self, manager):
        """Test deleting a nonexistent costume returns False."""
        result = manager.delete_costume("nonexistent")
        assert result is False

    def test_list_costumes(self, manager, sample_costume):
        """Test listing all costumes."""
        manager.create_costume(sample_costume)
        manager.create_costume(Costume(
            name="villain_suit",
            character="Villain",
            pieces=[CostumePiece(name="Jacket", category="outerwear", color="black", material="wool")],
        ))
        costumes = manager.list_costumes()
        assert len(costumes) == 2

    def test_list_costumes_by_character(self, manager, sample_costume):
        """Test listing costumes filtered by character."""
        manager.create_costume(sample_costume)
        manager.create_costume(Costume(
            name="villain_suit",
            character="Villain",
            pieces=[CostumePiece(name="Jacket", category="outerwear", color="black", material="wool")],
        ))
        costumes = manager.list_costumes(character="Hero")
        assert len(costumes) == 1
        assert costumes[0].name == "hero_casual"


class TestAssignment:
    """Tests for costume assignment operations."""

    def test_assign_costume(self, manager, sample_costume):
        """Test assigning a costume to a scene."""
        manager.create_costume(sample_costume)
        assignment = manager.assign_costume("Hero", 1, "hero_casual")
        assert assignment.character == "Hero"
        assert assignment.scene == 1
        assert assignment.costume == "hero_casual"

    def test_assign_nonexistent_costume(self, manager):
        """Test assigning a nonexistent costume raises error."""
        with pytest.raises(CostumeNotFoundError):
            manager.assign_costume("Hero", 1, "nonexistent")

    def test_assign_costume_with_condition(self, manager, sample_costume):
        """Test assigning a costume with specific condition."""
        manager.create_costume(sample_costume)
        assignment = manager.assign_costume("Hero", 1, "hero_casual", condition="dirty")
        assert assignment.condition == "dirty"

    def test_assign_costume_with_modifications(self, manager, sample_costume):
        """Test assigning a costume with modifications."""
        manager.create_costume(sample_costume)
        assignment = manager.assign_costume(
            "Hero", 1, "hero_casual",
            modifications=["rolled sleeves", "untucked"]
        )
        assert len(assignment.modifications) == 2

    def test_update_existing_assignment(self, manager, sample_costume):
        """Test updating an existing assignment."""
        manager.create_costume(sample_costume)
        manager.assign_costume("Hero", 1, "hero_casual")
        manager.assign_costume("Hero", 1, "hero_casual", condition="dirty")

        assignment = manager.get_costume_for_scene("Hero", 1)
        assert assignment.condition == "dirty"

    def test_get_costume_for_scene(self, manager, sample_costume):
        """Test getting costume for a specific scene."""
        manager.create_costume(sample_costume)
        manager.assign_costume("Hero", 1, "hero_casual")
        assignment = manager.get_costume_for_scene("Hero", 1)
        assert assignment is not None
        assert assignment.costume == "hero_casual"

    def test_get_costume_for_nonexistent_scene(self, manager):
        """Test getting costume for a scene with no assignment."""
        assignment = manager.get_costume_for_scene("Hero", 999)
        assert assignment is None

    def test_get_character_scenes(self, manager, sample_costume):
        """Test getting all scenes for a character."""
        manager.create_costume(sample_costume)
        manager.assign_costume("Hero", 1, "hero_casual")
        manager.assign_costume("Hero", 3, "hero_casual")
        manager.assign_costume("Hero", 5, "hero_casual")

        scenes = manager.get_character_scenes("Hero")
        assert len(scenes) == 3
        # Should be sorted by scene
        assert scenes[0].scene == 1
        assert scenes[1].scene == 3
        assert scenes[2].scene == 5

    def test_get_scene_assignments(self, manager, sample_costume):
        """Test getting all assignments for a scene."""
        manager.create_costume(sample_costume)
        manager.create_costume(Costume(
            name="villain_suit",
            character="Villain",
            pieces=[CostumePiece(name="Jacket", category="outerwear", color="black", material="wool")],
        ))
        manager.assign_costume("Hero", 1, "hero_casual")
        manager.assign_costume("Villain", 1, "villain_suit")

        assignments = manager.get_scene_assignments(1)
        assert len(assignments) == 2

    def test_remove_assignment(self, manager, sample_costume):
        """Test removing an assignment."""
        manager.create_costume(sample_costume)
        manager.assign_costume("Hero", 1, "hero_casual")
        result = manager.remove_assignment("Hero", 1)
        assert result is True
        assert manager.get_costume_for_scene("Hero", 1) is None


class TestChangeTracking:
    """Tests for costume change tracking."""

    def test_detect_costume_changes(self, manager, sample_costume):
        """Test detecting costume changes between scenes."""
        manager.create_costume(sample_costume)
        manager.create_costume(Costume(
            name="hero_formal",
            character="Hero",
            pieces=[CostumePiece(name="Suit", category="outerwear", color="black", material="wool")],
        ))
        manager.assign_costume("Hero", 1, "hero_casual")
        manager.assign_costume("Hero", 2, "hero_casual")
        manager.assign_costume("Hero", 5, "hero_formal")

        changes = manager.detect_costume_changes()
        assert len(changes) == 1
        assert changes[0].character == "Hero"
        assert changes[0].scene_before == 2
        assert changes[0].scene_after == 5

    def test_no_changes_detected(self, manager, sample_costume):
        """Test no changes detected when costume stays same."""
        manager.create_costume(sample_costume)
        manager.assign_costume("Hero", 1, "hero_casual")
        manager.assign_costume("Hero", 2, "hero_casual")
        manager.assign_costume("Hero", 3, "hero_casual")

        changes = manager.detect_costume_changes()
        assert len(changes) == 0

    def test_record_change(self, manager):
        """Test recording a costume change."""
        change = CostumeChange(
            character="Hero",
            scene_before=1,
            scene_after=5,
            costume_before="casual",
            costume_after="formal",
            change_reason="location",
        )
        manager.record_change(change)
        changes = manager.get_changes()
        assert len(changes) == 1

    def test_get_changes_by_character(self, manager):
        """Test getting changes for a specific character."""
        manager.record_change(CostumeChange(
            character="Hero",
            scene_before=1,
            scene_after=5,
            costume_before="casual",
            costume_after="formal",
        ))
        manager.record_change(CostumeChange(
            character="Villain",
            scene_before=2,
            scene_after=6,
            costume_before="suit",
            costume_after="combat",
        ))

        hero_changes = manager.get_changes(character="Hero")
        assert len(hero_changes) == 1


class TestQueryMethods:
    """Tests for query methods."""

    def test_get_all_costumes_for_character(self, manager, sample_costume):
        """Test getting all costumes for a character."""
        manager.create_costume(sample_costume)
        manager.create_costume(Costume(
            name="hero_formal",
            character="Hero",
            pieces=[CostumePiece(name="Suit", category="outerwear", color="black", material="wool")],
        ))
        costumes = manager.get_all_costumes_for_character("Hero")
        assert len(costumes) == 2

    def test_get_costume_usage(self, manager, sample_costume):
        """Test getting scenes where costume is used."""
        manager.create_costume(sample_costume)
        manager.assign_costume("Hero", 1, "hero_casual")
        manager.assign_costume("Hero", 3, "hero_casual")
        manager.assign_costume("Hero", 5, "hero_casual")

        scenes = manager.get_costume_usage("hero_casual")
        assert scenes == [1, 3, 5]

    def test_get_costume_usage_count(self, manager, sample_costume):
        """Test getting usage count for a costume."""
        manager.create_costume(sample_costume)
        manager.assign_costume("Hero", 1, "hero_casual")
        manager.assign_costume("Hero", 3, "hero_casual")

        count = manager.get_costume_usage_count("hero_casual")
        assert count == 2

    def test_find_costumes_by_color(self, manager, sample_costume):
        """Test finding costumes by color."""
        manager.create_costume(sample_costume)
        manager.create_costume(Costume(
            name="hero_formal",
            character="Hero",
            pieces=[CostumePiece(name="Suit", category="outerwear", color="black", material="wool")],
            colors=["black"],
        ))

        found = manager.find_costumes_by_color("navy")
        assert len(found) == 1
        assert found[0].name == "hero_casual"


class TestStatistics:
    """Tests for statistics methods."""

    def test_get_statistics(self, manager, sample_costume):
        """Test getting statistics."""
        manager.create_costume(sample_costume)
        manager.assign_costume("Hero", 1, "hero_casual")
        manager.assign_costume("Hero", 2, "hero_casual")

        stats = manager.get_statistics()
        assert stats["total_costumes"] == 1
        assert stats["total_assignments"] == 2
        assert stats["total_characters"] == 1

    def test_get_most_used_costumes(self, manager, sample_costume):
        """Test getting most used costumes."""
        manager.create_costume(sample_costume)
        manager.create_costume(Costume(
            name="hero_formal",
            character="Hero",
            pieces=[CostumePiece(name="Suit", category="outerwear", color="black", material="wool")],
        ))

        manager.assign_costume("Hero", 1, "hero_casual")
        manager.assign_costume("Hero", 2, "hero_casual")
        manager.assign_costume("Hero", 3, "hero_formal")

        most_used = manager.get_most_used_costumes()
        assert len(most_used) == 2
        assert most_used[0][0] == "hero_casual"
        assert most_used[0][1] == 2


class TestSerialization:
    """Tests for serialization methods."""

    def test_to_dict_and_from_dict(self, manager, sample_costume):
        """Test serialization round-trip."""
        manager.create_costume(sample_costume)
        manager.assign_costume("Hero", 1, "hero_casual")

        data = manager.to_dict()
        restored = CostumeManager.from_dict(data)

        assert restored.registry.production_name == manager.registry.production_name
        assert "hero_casual" in restored.registry.costumes

    def test_export_assignments_csv(self, manager, sample_costume):
        """Test exporting assignments as CSV."""
        manager.create_costume(sample_costume)
        manager.assign_costume("Hero", 1, "hero_casual")
        manager.assign_costume("Hero", 2, "hero_casual", condition="dirty")

        csv = manager.export_assignments_csv()
        lines = csv.strip().split("\n")
        assert len(lines) == 3  # header + 2 rows
        assert "character,scene,costume" in lines[0]

    def test_export_changes_csv(self, manager):
        """Test exporting changes as CSV."""
        manager.record_change(CostumeChange(
            character="Hero",
            scene_before=1,
            scene_after=5,
            costume_before="casual",
            costume_after="formal",
        ))

        csv = manager.export_changes_csv()
        lines = csv.strip().split("\n")
        assert len(lines) == 2  # header + 1 row
