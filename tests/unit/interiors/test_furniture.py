"""
Tests for Furniture Placer

Tests furniture placement based on room type and ergonomic rules.
"""

import pytest
from lib.interiors.furniture import (
    FurnitureCategory,
    FurnitureItem,
    FurnitureLayout,
    FurniturePlacer,
    FURNITURE_CATALOGS,
    place_furniture_in_room,
)
from lib.interiors.types import Room, DoorSpec


class TestFurnitureCategory:
    """Tests for FurnitureCategory enum."""

    def test_category_values(self):
        """Test FurnitureCategory enum values."""
        assert FurnitureCategory.SEATING.value == "seating"
        assert FurnitureCategory.TABLE.value == "table"
        assert FurnitureCategory.STORAGE.value == "storage"
        assert FurnitureCategory.BED.value == "bed"
        assert FurnitureCategory.DESK.value == "desk"


class TestFurnitureItem:
    """Tests for FurnitureItem dataclass."""

    def test_create_default(self):
        """Test creating FurnitureItem with defaults."""
        item = FurnitureItem()
        assert item.name == ""
        assert item.category == "decor"
        assert item.dimensions == (0.5, 0.5, 0.5)

    def test_create_with_values(self):
        """Test creating FurnitureItem with values."""
        item = FurnitureItem(
            name="sofa",
            category="seating",
            dimensions=(2.2, 0.9, 0.85),
            wall_required=True,
            clearance=0.8,
        )
        assert item.name == "sofa"
        assert item.wall_required is True
        assert item.clearance == 0.8

    def test_to_dict(self):
        """Test FurnitureItem serialization."""
        item = FurnitureItem(name="chair", dimensions=(0.5, 0.5, 0.9))
        result = item.to_dict()
        assert result["name"] == "chair"
        assert result["dimensions"] == [0.5, 0.5, 0.9]


class TestFurnitureCatalogs:
    """Tests for FURNITURE_CATALOGS."""

    def test_catalogs_exist(self):
        """Test that catalogs are populated."""
        assert isinstance(FURNITURE_CATALOGS, dict)
        assert len(FURNITURE_CATALOGS) > 0

    def test_living_room_catalog(self):
        """Test living room catalog."""
        assert "living_room" in FURNITURE_CATALOGS
        items = FURNITURE_CATALOGS["living_room"]
        assert len(items) > 0

        # Check for essential items
        names = [item.name for item in items]
        assert any("sofa" in name for name in names)

    def test_bedroom_catalog(self):
        """Test bedroom catalog."""
        assert "bedroom" in FURNITURE_CATALOGS
        items = FURNITURE_CATALOGS["bedroom"]
        assert len(items) > 0

    def test_kitchen_catalog(self):
        """Test kitchen catalog."""
        assert "kitchen" in FURNITURE_CATALOGS
        items = FURNITURE_CATALOGS["kitchen"]
        assert len(items) > 0

    def test_bathroom_catalog(self):
        """Test bathroom catalog."""
        assert "bathroom" in FURNITURE_CATALOGS
        items = FURNITURE_CATALOGS["bathroom"]
        assert len(items) > 0

    def test_all_items_have_required_fields(self):
        """Test that all catalog items have required fields."""
        for room_type, items in FURNITURE_CATALOGS.items():
            for item in items:
                assert item.name, f"Item in {room_type} missing name"
                assert item.dimensions[0] > 0, f"Item {item.name} has invalid width"
                assert item.clearance >= 0, f"Item {item.name} has invalid clearance"


class TestFurnitureLayout:
    """Tests for FurnitureLayout dataclass."""

    def test_create_default(self):
        """Test creating FurnitureLayout with defaults."""
        layout = FurnitureLayout()
        assert layout.room_id == ""
        assert layout.items == []
        assert layout.total_items == 0
        assert layout.coverage == 0.0

    def test_create_with_values(self):
        """Test creating FurnitureLayout with values."""
        from lib.interiors.types import FurniturePlacement
        items = [FurniturePlacement(furniture_type="sofa")]
        layout = FurnitureLayout(
            room_id="r1",
            items=items,
            total_items=1,
            coverage=0.3,
        )
        assert layout.room_id == "r1"
        assert layout.coverage == 0.3

    def test_to_dict(self):
        """Test FurnitureLayout serialization."""
        layout = FurnitureLayout(room_id="test", total_items=5)
        result = layout.to_dict()
        assert result["room_id"] == "test"
        assert result["total_items"] == 5


class TestFurniturePlacer:
    """Tests for FurniturePlacer class."""

    def test_init(self):
        """Test FurniturePlacer initialization."""
        placer = FurniturePlacer()
        assert placer.seed is None

    def test_init_with_seed(self):
        """Test FurniturePlacer initialization with seed."""
        placer = FurniturePlacer(seed=42)
        assert placer.seed == 42

    def test_place_furniture_living_room(self):
        """Test placing furniture in living room."""
        placer = FurniturePlacer()
        room = Room(
            id="r1",
            room_type="living_room",
            polygon=[(0, 0), (6, 0), (6, 5), (0, 5)],
        )
        layout = placer.place_furniture(room)

        assert layout.room_id == "r1"
        assert len(layout.items) > 0

    def test_place_furniture_bedroom(self):
        """Test placing furniture in bedroom."""
        placer = FurniturePlacer()
        room = Room(
            id="r1",
            room_type="bedroom",
            polygon=[(0, 0), (4, 0), (4, 4), (0, 4)],
        )
        layout = placer.place_furniture(room)

        assert len(layout.items) > 0

    def test_place_furniture_kitchen(self):
        """Test placing furniture in kitchen."""
        placer = FurniturePlacer()
        room = Room(
            id="r1",
            room_type="kitchen",
            polygon=[(0, 0), (4, 0), (4, 3), (0, 3)],
        )
        layout = placer.place_furniture(room)

        assert len(layout.items) > 0

    def test_place_furniture_bathroom(self):
        """Test placing furniture in bathroom."""
        placer = FurniturePlacer()
        room = Room(
            id="r1",
            room_type="bathroom",
            polygon=[(0, 0), (2, 0), (2, 2.5), (0, 2.5)],
        )
        layout = placer.place_furniture(room)

        assert len(layout.items) > 0

    def test_place_furniture_office(self):
        """Test placing furniture in office."""
        placer = FurniturePlacer()
        room = Room(
            id="r1",
            room_type="office",
            polygon=[(0, 0), (4, 0), (4, 3), (0, 3)],
        )
        layout = placer.place_furniture(room)

        assert len(layout.items) > 0

    def test_place_furniture_max_items(self):
        """Test max items limit."""
        placer = FurniturePlacer()
        room = Room(
            id="r1",
            room_type="living_room",
            polygon=[(0, 0), (10, 0), (10, 10), (0, 10)],
        )
        layout = placer.place_furniture(room, max_items=3)

        assert len(layout.items) <= 3

    def test_item_fits_true(self):
        """Test item fitting check - fits."""
        placer = FurniturePlacer()
        item = FurnitureItem(dimensions=(1.0, 0.5, 0.8), clearance=0.5)
        fits = placer._item_fits(item, room_width=3.0, room_depth=2.0)
        assert fits is True

    def test_item_fits_false(self):
        """Test item fitting check - doesn't fit."""
        placer = FurniturePlacer()
        item = FurnitureItem(dimensions=(2.0, 1.5, 0.8), clearance=0.5)
        fits = placer._item_fits(item, room_width=2.0, room_depth=1.5)
        assert fits is False

    def test_calculate_placement_centered(self):
        """Test placement calculation - centered."""
        placer = FurniturePlacer()
        item = FurnitureItem(name="table", centered=True)
        pos = placer._calculate_placement(
            item,
            center=(5, 5),
            bounds=(0, 0, 10, 10),
            room_width=10,
            room_depth=10,
        )
        assert pos == (5, 5, 0.0)

    def test_coverage_calculation(self):
        """Test coverage calculation."""
        placer = FurniturePlacer()
        room = Room(
            id="r1",
            room_type="living_room",
            polygon=[(0, 0), (5, 0), (5, 5), (0, 5)],
        )
        layout = placer.place_furniture(room)

        # Coverage should be between 0 and 1
        assert 0.0 <= layout.coverage <= 1.0

    def test_unknown_room_type(self):
        """Test handling unknown room type."""
        placer = FurniturePlacer()
        room = Room(
            id="r1",
            room_type="unknown_room_type",
            polygon=[(0, 0), (5, 0), (5, 4), (0, 4)],
        )
        layout = placer.place_furniture(room)

        # Should fall back to living room catalog
        assert layout.room_id == "r1"


class TestPlaceFurnitureInRoom:
    """Tests for place_furniture_in_room function."""

    def test_place(self):
        """Test place_furniture_in_room function."""
        room = Room(
            id="r1",
            room_type="living_room",
            polygon=[(0, 0), (6, 0), (6, 5), (0, 5)],
        )
        layout = place_furniture_in_room(room)

        assert layout.room_id == "r1"
        assert len(layout.items) > 0

    def test_place_with_max_items(self):
        """Test with max_items parameter."""
        room = Room(
            id="r1",
            room_type="living_room",
            polygon=[(0, 0), (6, 0), (6, 5), (0, 5)],
        )
        layout = place_furniture_in_room(room, max_items=5)

        assert len(layout.items) <= 5

    def test_place_with_seed(self):
        """Test with seed parameter."""
        room = Room(
            id="r1",
            room_type="living_room",
            polygon=[(0, 0), (6, 0), (6, 5), (0, 5)],
        )
        layout = place_furniture_in_room(room, seed=42)

        assert layout is not None


class TestFurniturePlacerEdgeCases:
    """Edge case tests for furniture placer."""

    def test_very_small_room(self):
        """Test placing in very small room."""
        placer = FurniturePlacer()
        room = Room(
            id="r1",
            room_type="living_room",
            polygon=[(0, 0), (2, 0), (2, 2), (0, 2)],
        )
        layout = placer.place_furniture(room)

        # Should still place some furniture, just fewer items
        assert isinstance(layout.items, list)

    def test_very_large_room(self):
        """Test placing in very large room."""
        placer = FurniturePlacer()
        room = Room(
            id="r1",
            room_type="living_room",
            polygon=[(0, 0), (20, 0), (20, 15), (0, 15)],
        )
        layout = placer.place_furniture(room, max_items=20)

        assert len(layout.items) <= 20

    def test_narrow_room(self):
        """Test placing in narrow room."""
        placer = FurniturePlacer()
        room = Room(
            id="r1",
            room_type="hallway",
            polygon=[(0, 0), (1.5, 0), (1.5, 10), (0, 10)],
        )
        layout = placer.place_furniture(room)

        assert isinstance(layout.items, list)

    def test_empty_room_catalog(self):
        """Test room type with no catalog entries."""
        placer = FurniturePlacer()
        room = Room(
            id="r1",
            room_type="nonexistent_type",
            polygon=[(0, 0), (5, 0), (5, 4), (0, 4)],
        )
        layout = placer.place_furniture(room)

        # Should fall back to living room
        assert layout is not None
