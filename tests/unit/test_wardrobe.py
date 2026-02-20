"""
Tests for Wardrobe System - Types

Tests for wardrobe_types.py data structures.
"""

import pytest
from datetime import datetime

from lib.character.wardrobe_types import (
    CostumePiece,
    Costume,
    CostumeChange,
    CostumeAssignment,
    WardrobeRegistry,
    CostumeCategory,
    CostumeStyle,
    CostumeCondition,
    ChangeReason,
    IssueType,
    IssueSeverity,
    CONDITION_PROGRESSION,
    is_valid_condition_progression,
)


class TestCostumePiece:
    """Tests for CostumePiece dataclass."""

    def test_create_piece(self):
        """Test creating a costume piece."""
        piece = CostumePiece(
            name="T-Shirt",
            category="top",
            color="blue",
            material="cotton",
        )
        assert piece.name == "T-Shirt"
        assert piece.category == "top"
        assert piece.color == "blue"
        assert piece.material == "cotton"
        assert piece.style == "casual"  # default

    def test_piece_to_dict(self):
        """Test converting piece to dictionary."""
        piece = CostumePiece(
            name="Jeans",
            category="bottom",
            color="dark blue",
            material="denim",
            style="casual",
            brand="Levi's",
        )
        data = piece.to_dict()
        assert data["name"] == "Jeans"
        assert data["category"] == "bottom"
        assert data["color"] == "dark blue"
        assert data["brand"] == "Levi's"

    def test_piece_from_dict(self):
        """Test creating piece from dictionary."""
        data = {
            "name": "Sneakers",
            "category": "shoes",
            "color": "white",
            "material": "canvas",
            "style": "casual",
        }
        piece = CostumePiece.from_dict(data)
        assert piece.name == "Sneakers"
        assert piece.category == "shoes"

    def test_piece_matches_strict(self):
        """Test strict piece matching."""
        piece1 = CostumePiece(
            name="Shirt",
            category="top",
            color="blue",
            material="cotton",
        )
        piece2 = CostumePiece(
            name="Shirt",
            category="top",
            color="blue",
            material="cotton",
        )
        piece3 = CostumePiece(
            name="Shirt",
            category="top",
            color="red",  # Different color
            material="cotton",
        )
        assert piece1.matches(piece2, strict=True)
        assert not piece1.matches(piece3, strict=True)

    def test_piece_matches_non_strict(self):
        """Test non-strict piece matching."""
        piece1 = CostumePiece(
            name="Shirt",
            category="top",
            color="Blue",  # Different case
            material="polyester",  # Different material
        )
        piece2 = CostumePiece(
            name="Shirt",
            category="top",
            color="blue",
            material="cotton",
        )
        # Non-strict: same name and color (case-insensitive)
        assert piece1.matches(piece2, strict=False)


class TestCostume:
    """Tests for Costume dataclass."""

    def test_create_costume(self):
        """Test creating a costume."""
        costume = Costume(
            name="hero_casual",
            character="Hero",
            pieces=[
                CostumePiece(name="Shirt", category="top", color="blue", material="cotton"),
            ],
            colors=["blue"],
        )
        assert costume.name == "hero_casual"
        assert costume.character == "Hero"
        assert len(costume.pieces) == 1
        assert costume.condition == "pristine"

    def test_get_piece(self):
        """Test getting piece by category."""
        costume = Costume(
            name="test",
            character="Test",
            pieces=[
                CostumePiece(name="Shirt", category="top", color="blue", material="cotton"),
                CostumePiece(name="Pants", category="bottom", color="black", material="denim"),
            ],
        )
        top = costume.get_piece("top")
        assert top is not None
        assert top.name == "Shirt"

        shoes = costume.get_piece("shoes")
        assert shoes is None

    def test_get_all_pieces(self):
        """Test getting all pieces including accessories."""
        costume = Costume(
            name="test",
            character="Test",
            pieces=[
                CostumePiece(name="Shirt", category="top", color="blue", material="cotton"),
            ],
            accessories=[
                CostumePiece(name="Watch", category="accessory", color="silver", material="metal"),
            ],
        )
        all_pieces = costume.get_all_pieces()
        assert len(all_pieces) == 2

    def test_costume_matches(self):
        """Test costume matching."""
        costume1 = Costume(
            name="hero_casual",
            character="Hero",
            pieces=[
                CostumePiece(name="Shirt", category="top", color="blue", material="cotton"),
            ],
        )
        costume2 = Costume(
            name="hero_casual",
            character="Hero",
            pieces=[
                CostumePiece(name="Shirt", category="top", color="blue", material="cotton"),
            ],
        )
        costume3 = Costume(
            name="hero_formal",
            character="Hero",
            pieces=[
                CostumePiece(name="Jacket", category="outerwear", color="black", material="wool"),
            ],
        )
        assert costume1.matches(costume2)
        assert not costume1.matches(costume3)

    def test_costume_to_dict(self):
        """Test converting costume to dictionary."""
        costume = Costume(
            name="test",
            character="Test",
            pieces=[
                CostumePiece(name="Shirt", category="top", color="blue", material="cotton"),
            ],
            colors=["blue"],
            condition="pristine",
        )
        data = costume.to_dict()
        assert data["name"] == "test"
        assert data["character"] == "Test"
        assert len(data["pieces"]) == 1
        assert data["colors"] == ["blue"]

    def test_costume_from_dict(self):
        """Test creating costume from dictionary."""
        data = {
            "name": "test",
            "character": "Test",
            "pieces": [
                {"name": "Shirt", "category": "top", "color": "blue", "material": "cotton"}
            ],
            "colors": ["blue"],
            "condition": "worn",
        }
        costume = Costume.from_dict(data)
        assert costume.name == "test"
        assert costume.condition == "worn"
        assert len(costume.pieces) == 1

    def test_get_total_cost(self):
        """Test calculating total costume cost."""
        costume = Costume(
            name="test",
            character="Test",
            pieces=[
                CostumePiece(name="Shirt", category="top", color="blue", material="cotton", estimated_cost=50.0),
                CostumePiece(name="Pants", category="bottom", color="black", material="denim", estimated_cost=80.0),
            ],
            accessories=[
                CostumePiece(name="Watch", category="accessory", color="silver", material="metal", estimated_cost=150.0),
            ],
        )
        assert costume.get_total_cost() == 280.0


class TestCostumeChange:
    """Tests for CostumeChange dataclass."""

    def test_create_change(self):
        """Test creating a costume change."""
        change = CostumeChange(
            character="Hero",
            scene_before=1,
            scene_after=5,
            costume_before="hero_casual",
            costume_after="hero_formal",
            change_reason="location",
        )
        assert change.character == "Hero"
        assert change.scene_before == 1
        assert change.scene_after == 5
        assert change.change_reason == "location"

    def test_change_to_dict(self):
        """Test converting change to dictionary."""
        change = CostumeChange(
            character="Hero",
            scene_before=1,
            scene_after=5,
            costume_before="casual",
            costume_after="formal",
        )
        data = change.to_dict()
        assert data["character"] == "Hero"
        assert data["scene_before"] == 1

    def test_change_from_dict(self):
        """Test creating change from dictionary."""
        data = {
            "character": "Hero",
            "scene_before": 1,
            "scene_after": 5,
            "costume_before": "casual",
            "costume_after": "formal",
            "change_reason": "story",
        }
        change = CostumeChange.from_dict(data)
        assert change.character == "Hero"


class TestCostumeAssignment:
    """Tests for CostumeAssignment dataclass."""

    def test_create_assignment(self):
        """Test creating an assignment."""
        assignment = CostumeAssignment(
            character="Hero",
            scene=1,
            costume="hero_casual",
            condition="pristine",
        )
        assert assignment.character == "Hero"
        assert assignment.scene == 1
        assert assignment.costume == "hero_casual"
        assert assignment.modifications == []

    def test_assignment_to_dict(self):
        """Test converting assignment to dictionary."""
        assignment = CostumeAssignment(
            character="Hero",
            scene=1,
            costume="hero_casual",
            condition="dirty",
            modifications=["rolled sleeves"],
        )
        data = assignment.to_dict()
        assert data["character"] == "Hero"
        assert data["modifications"] == ["rolled sleeves"]


class TestWardrobeRegistry:
    """Tests for WardrobeRegistry dataclass."""

    def test_create_registry(self):
        """Test creating a registry."""
        registry = WardrobeRegistry(production_name="Test Production")
        assert registry.production_name == "Test Production"
        assert len(registry.costumes) == 0

    def test_add_costume(self):
        """Test adding a costume."""
        registry = WardrobeRegistry()
        costume = Costume(
            name="hero_casual",
            character="Hero",
            pieces=[
                CostumePiece(name="Shirt", category="top", color="blue", material="cotton"),
            ],
        )
        registry.add_costume(costume)
        assert "hero_casual" in registry.costumes
        assert "Hero" in registry.characters
        assert "hero_casual" in registry.characters["Hero"]

    def test_remove_costume(self):
        """Test removing a costume."""
        registry = WardrobeRegistry()
        costume = Costume(
            name="hero_casual",
            character="Hero",
            pieces=[
                CostumePiece(name="Shirt", category="top", color="blue", material="cotton"),
            ],
        )
        registry.add_costume(costume)
        result = registry.remove_costume("hero_casual")
        assert result is True
        assert "hero_casual" not in registry.costumes

    def test_get_costume(self):
        """Test getting a costume."""
        registry = WardrobeRegistry()
        costume = Costume(
            name="hero_casual",
            character="Hero",
            pieces=[
                CostumePiece(name="Shirt", category="top", color="blue", material="cotton"),
            ],
        )
        registry.add_costume(costume)
        retrieved = registry.get_costume("hero_casual")
        assert retrieved is not None
        assert retrieved.name == "hero_casual"

    def test_get_costumes_for_character(self):
        """Test getting costumes for a character."""
        registry = WardrobeRegistry()
        registry.add_costume(Costume(
            name="hero_casual",
            character="Hero",
            pieces=[CostumePiece(name="Shirt", category="top", color="blue", material="cotton")],
        ))
        registry.add_costume(Costume(
            name="hero_formal",
            character="Hero",
            pieces=[CostumePiece(name="Suit", category="outerwear", color="black", material="wool")],
        ))
        registry.add_costume(Costume(
            name="villain_suit",
            character="Villain",
            pieces=[CostumePiece(name="Jacket", category="outerwear", color="black", material="wool")],
        ))
        costumes = registry.get_costumes_for_character("Hero")
        assert len(costumes) == 2

    def test_add_and_get_assignment(self):
        """Test adding and getting assignments."""
        registry = WardrobeRegistry()
        assignment = CostumeAssignment(
            character="Hero",
            scene=1,
            costume="hero_casual",
        )
        registry.add_assignment(assignment)
        retrieved = registry.get_assignment("Hero", 1)
        assert retrieved is not None
        assert retrieved.costume == "hero_casual"

    def test_get_assignments_for_scene(self):
        """Test getting assignments for a scene."""
        registry = WardrobeRegistry()
        registry.add_assignment(CostumeAssignment(character="Hero", scene=1, costume="hero_casual"))
        registry.add_assignment(CostumeAssignment(character="Villain", scene=1, costume="villain_suit"))
        registry.add_assignment(CostumeAssignment(character="Hero", scene=2, costume="hero_formal"))
        assignments = registry.get_assignments_for_scene(1)
        assert len(assignments) == 2

    def test_get_all_characters(self):
        """Test getting all characters."""
        registry = WardrobeRegistry()
        registry.add_costume(Costume(
            name="hero_casual",
            character="Hero",
            pieces=[CostumePiece(name="Shirt", category="top", color="blue", material="cotton")],
        ))
        registry.add_costume(Costume(
            name="villain_suit",
            character="Villain",
            pieces=[CostumePiece(name="Jacket", category="outerwear", color="black", material="wool")],
        ))
        characters = registry.get_all_characters()
        assert "Hero" in characters
        assert "Villain" in characters

    def test_registry_to_dict_and_from_dict(self):
        """Test serialization round-trip."""
        registry = WardrobeRegistry(production_name="Test")
        registry.add_costume(Costume(
            name="hero_casual",
            character="Hero",
            pieces=[CostumePiece(name="Shirt", category="top", color="blue", material="cotton")],
            colors=["blue"],
        ))
        registry.add_assignment(CostumeAssignment(
            character="Hero",
            scene=1,
            costume="hero_casual",
        ))

        data = registry.to_dict()
        restored = WardrobeRegistry.from_dict(data)

        assert restored.production_name == "Test"
        assert "hero_casual" in restored.costumes
        assert len(restored.assignments) == 1


class TestConditionProgression:
    """Tests for condition progression rules."""

    def test_valid_progression_pristine_to_worn(self):
        """Test pristine to worn is valid."""
        assert is_valid_condition_progression("pristine", "worn")

    def test_valid_progression_pristine_to_dirty(self):
        """Test pristine to dirty is valid."""
        assert is_valid_condition_progression("pristine", "dirty")

    def test_invalid_progression_damaged_to_pristine(self):
        """Test damaged to pristine is invalid."""
        assert not is_valid_condition_progression("damaged", "pristine")

    def test_invalid_progression_torn_to_pristine(self):
        """Test torn to pristine is invalid."""
        assert not is_valid_condition_progression("torn", "pristine")

    def test_valid_progression_dirty_to_pristine(self):
        """Test dirty to pristine is valid (cleaning)."""
        assert is_valid_condition_progression("dirty", "pristine")

    def test_valid_progression_wet_to_pristine(self):
        """Test wet to pristine is valid (drying)."""
        assert is_valid_condition_progression("wet", "pristine")

    def test_condition_progression_dict_exists(self):
        """Test CONDITION_PROGRESSION dictionary exists with expected keys."""
        assert "pristine" in CONDITION_PROGRESSION
        assert "damaged" in CONDITION_PROGRESSION
        assert "bloodied" in CONDITION_PROGRESSION
        assert "torn" in CONDITION_PROGRESSION


class TestEnums:
    """Tests for enum values."""

    def test_costume_category_values(self):
        """Test CostumeCategory enum values."""
        assert CostumeCategory.TOP.value == "top"
        assert CostumeCategory.BOTTOM.value == "bottom"
        assert CostumeCategory.SHOES.value == "shoes"

    def test_costume_style_values(self):
        """Test CostumeStyle enum values."""
        assert CostumeStyle.CASUAL.value == "casual"
        assert CostumeStyle.FORMAL.value == "formal"
        assert CostumeStyle.PERIOD.value == "period"

    def test_costume_condition_values(self):
        """Test CostumeCondition enum values."""
        assert CostumeCondition.PRISTINE.value == "pristine"
        assert CostumeCondition.DAMAGED.value == "damaged"
        assert CostumeCondition.BLOODIED.value == "bloodied"

    def test_change_reason_values(self):
        """Test ChangeReason enum values."""
        assert ChangeReason.STORY.value == "story"
        assert ChangeReason.LOCATION.value == "location"
        assert ChangeReason.DAMAGE.value == "damage"

    def test_issue_type_values(self):
        """Test IssueType enum values."""
        assert IssueType.COSTUME_MISMATCH.value == "costume_mismatch"
        assert IssueType.MISSING_ASSIGNMENT.value == "missing_assignment"

    def test_issue_severity_values(self):
        """Test IssueSeverity enum values."""
        assert IssueSeverity.ERROR.value == "error"
        assert IssueSeverity.WARNING.value == "warning"
        assert IssueSeverity.INFO.value == "info"
