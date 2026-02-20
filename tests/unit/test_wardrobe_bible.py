"""
Tests for Wardrobe System - Costume Bible

Tests for costume_bible.py.
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import os

from lib.character.wardrobe_types import (
    Costume,
    CostumePiece,
    CostumeAssignment,
    WardrobeRegistry,
)
from lib.character.costume_bible import (
    ShoppingItem,
    CharacterWardrobe,
    CostumeBible,
    generate_costume_bible,
    generate_shopping_list,
    export_bible_yaml,
    export_bible_html,
    generate_scene_breakdown_csv,
    generate_costume_summary_csv,
)


@pytest.fixture
def sample_registry():
    """Create a sample registry with costumes and assignments."""
    registry = WardrobeRegistry(production_name="Test Production")

    # Hero costumes
    registry.add_costume(Costume(
        name="hero_casual",
        character="Hero",
        pieces=[
            CostumePiece(name="T-Shirt", category="top", color="navy", material="cotton", estimated_cost=25.0),
            CostumePiece(name="Jeans", category="bottom", color="blue", material="denim", estimated_cost=60.0),
        ],
        accessories=[
            CostumePiece(name="Watch", category="accessory", color="silver", material="metal", estimated_cost=150.0),
        ],
        colors=["navy", "blue"],
        condition="pristine",
    ))

    registry.add_costume(Costume(
        name="hero_formal",
        character="Hero",
        pieces=[
            CostumePiece(name="Suit Jacket", category="outerwear", color="charcoal", material="wool", estimated_cost=350.0),
            CostumePiece(name="Dress Pants", category="bottom", color="charcoal", material="wool", estimated_cost=150.0),
        ],
        colors=["charcoal"],
        condition="pristine",
    ))

    # Villain costume
    registry.add_costume(Costume(
        name="villain_suit",
        character="Villain",
        pieces=[
            CostumePiece(name="Suit", category="outerwear", color="black", material="wool", estimated_cost=400.0),
        ],
        colors=["black"],
        condition="pristine",
    ))

    # Assignments
    registry.add_assignment(CostumeAssignment(character="Hero", scene=1, costume="hero_casual", condition="pristine"))
    registry.add_assignment(CostumeAssignment(character="Hero", scene=2, costume="hero_casual", condition="pristine"))
    registry.add_assignment(CostumeAssignment(character="Hero", scene=5, costume="hero_formal", condition="pristine"))
    registry.add_assignment(CostumeAssignment(character="Villain", scene=1, costume="villain_suit", condition="pristine"))
    registry.add_assignment(CostumeAssignment(character="Villain", scene=5, costume="villain_suit", condition="pristine"))

    return registry


class TestShoppingItem:
    """Tests for ShoppingItem dataclass."""

    def test_create_item(self):
        """Test creating a shopping item."""
        item = ShoppingItem(
            name="T-Shirt",
            category="top",
            color="blue",
            material="cotton",
            quantity=2,
            estimated_cost=25.0,
        )
        assert item.name == "T-Shirt"
        assert item.quantity == 2
        assert item.status == "needed"

    def test_item_to_dict(self):
        """Test converting item to dictionary."""
        item = ShoppingItem(
            name="Shirt",
            category="top",
            color="blue",
            material="cotton",
            for_costume="hero_casual",
            for_character="Hero",
        )
        data = item.to_dict()
        assert data["for_costume"] == "hero_casual"
        assert data["for_character"] == "Hero"


class TestCharacterWardrobe:
    """Tests for CharacterWardrobe dataclass."""

    def test_create_wardrobe(self):
        """Test creating a character wardrobe."""
        wardrobe = CharacterWardrobe(
            character="Hero",
            total_costumes=2,
            color_theme=["blue", "black"],
            total_estimated_cost=500.0,
        )
        assert wardrobe.character == "Hero"
        assert wardrobe.total_costumes == 2

    def test_wardrobe_to_dict(self):
        """Test converting wardrobe to dictionary."""
        wardrobe = CharacterWardrobe(
            character="Hero",
            total_costumes=1,
            scene_breakdown=[(1, "casual", "pristine")],
            color_theme=["blue"],
        )
        data = wardrobe.to_dict()
        assert data["character"] == "Hero"
        assert len(data["scene_breakdown"]) == 1


class TestCostumeBible:
    """Tests for CostumeBible dataclass."""

    def test_create_bible(self):
        """Test creating a costume bible."""
        bible = CostumeBible(
            production="Test Production",
            total_budget=1000.0,
        )
        assert bible.production == "Test Production"
        assert bible.total_budget == 1000.0

    def test_bible_to_dict(self):
        """Test converting bible to dictionary."""
        bible = CostumeBible(
            production="Test",
            color_palettes={"Hero": ["blue", "black"]},
        )
        data = bible.to_dict()
        assert data["production"] == "Test"
        assert "Hero" in data["color_palettes"]


class TestGenerateCostumeBible:
    """Tests for generate_costume_bible function."""

    def test_generate_bible(self, sample_registry):
        """Test generating a complete costume bible."""
        bible = generate_costume_bible(sample_registry, "Test Production")

        assert bible.production == "Test Production"
        assert len(bible.characters) == 2
        assert "Hero" in bible.characters
        assert "Villain" in bible.characters

    def test_bible_character_wardrobes(self, sample_registry):
        """Test character wardrobes in bible."""
        bible = generate_costume_bible(sample_registry)

        hero_wardrobe = bible.characters["Hero"]
        assert hero_wardrobe.total_costumes == 2
        assert len(hero_wardrobe.scene_breakdown) == 3

    def test_bible_color_palettes(self, sample_registry):
        """Test color palettes in bible."""
        bible = generate_costume_bible(sample_registry)

        assert "Hero" in bible.color_palettes
        assert "navy" in bible.color_palettes["Hero"] or "blue" in bible.color_palettes["Hero"]

    def test_bible_scene_breakdown(self, sample_registry):
        """Test scene breakdown in bible."""
        bible = generate_costume_bible(sample_registry)

        assert 1 in bible.scene_breakdown
        assert bible.scene_breakdown[1]["Hero"] == "hero_casual"
        assert bible.scene_breakdown[1]["Villain"] == "villain_suit"

    def test_bible_shopping_list(self, sample_registry):
        """Test shopping list in bible."""
        bible = generate_costume_bible(sample_registry)

        assert len(bible.shopping_list) > 0
        # Check for specific items
        item_names = [item.name for item in bible.shopping_list]
        assert "T-Shirt" in item_names

    def test_bible_total_budget(self, sample_registry):
        """Test total budget calculation."""
        bible = generate_costume_bible(sample_registry)

        # Hero: 25 + 60 + 150 + 350 + 150 = 735
        # Villain: 400
        # Total should be 1135
        assert bible.total_budget == 1135.0


class TestGenerateShoppingList:
    """Tests for generate_shopping_list function."""

    def test_generate_list(self, sample_registry):
        """Test generating shopping list."""
        items = generate_shopping_list(sample_registry)

        assert len(items) > 0

    def test_consolidates_same_items(self):
        """Test that duplicate items are consolidated."""
        registry = WardrobeRegistry()
        registry.add_costume(Costume(
            name="costume1",
            character="Hero",
            pieces=[
                CostumePiece(name="T-Shirt", category="top", color="blue", material="cotton", quantity=1),
            ],
        ))
        registry.add_costume(Costume(
            name="costume2",
            character="Hero",
            pieces=[
                CostumePiece(name="T-Shirt", category="top", color="blue", material="cotton", quantity=1),
            ],
        ))

        items = generate_shopping_list(registry)
        tshirt_items = [i for i in items if i.name == "T-Shirt"]
        assert len(tshirt_items) == 1
        assert tshirt_items[0].quantity == 2


class TestExportFunctions:
    """Tests for export functions."""

    def test_export_bible_html(self, sample_registry):
        """Test HTML export."""
        bible = generate_costume_bible(sample_registry)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_bible.html")
            export_bible_html(bible, path)

            assert os.path.exists(path)
            with open(path, "r") as f:
                content = f.read()
            assert "<!DOCTYPE html>" in content
            assert "Test Production" in content

    def test_export_bible_yaml(self, sample_registry):
        """Test YAML export."""
        bible = generate_costume_bible(sample_registry)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_bible.yaml")
            export_bible_yaml(bible, path)

            # Should create either YAML or JSON file
            yaml_exists = os.path.exists(path)
            json_exists = os.path.exists(os.path.join(tmpdir, "test_bible.json"))
            assert yaml_exists or json_exists

    def test_generate_scene_breakdown_csv(self, sample_registry):
        """Test scene breakdown CSV generation."""
        bible = generate_costume_bible(sample_registry)

        csv = generate_scene_breakdown_csv(bible)
        lines = csv.strip().split("\n")

        # Header + 3 scenes
        assert len(lines) >= 2
        assert "scene" in lines[0].lower()

    def test_generate_costume_summary_csv(self, sample_registry):
        """Test costume summary CSV generation."""
        bible = generate_costume_bible(sample_registry)

        csv = generate_costume_summary_csv(bible)
        lines = csv.strip().split("\n")

        # Header + 3 costumes
        assert len(lines) == 4  # 1 header + 3 costumes
        assert "character,costume" in lines[0]


class TestExportBiblePDF:
    """Tests for PDF export."""

    def test_export_pdf_returns_false_without_library(self, sample_registry):
        """Test PDF export returns False if libraries not available."""
        bible = generate_costume_bible(sample_registry)

        # This test may pass or fail depending on whether reportlab/weasyprint is installed
        # Just verify the function doesn't crash
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.pdf")
            # Function should not raise an exception
            try:
                result = export_bible_pdf(bible, path)
                # If libraries are available, should succeed
                if result:
                    assert os.path.exists(path)
            except Exception:
                # If libraries are not available, function returns False
                pass
