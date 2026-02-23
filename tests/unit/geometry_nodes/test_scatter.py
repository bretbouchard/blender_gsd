"""
Unit tests for lib/geometry_nodes/scatter.py

Tests the furniture scatter system including:
- PlacementStrategy enum
- FurnitureCategory enum
- FurnitureBounds dataclass
- PlacementConstraint dataclass
- FurnitureItem dataclass
- PlacedItem dataclass
- ScatterResult dataclass
- FURNITURE_CATALOG
- ROOM_FURNITURE_SETS
- FurnitureScatterer class
- scatter_furniture function
"""

import pytest
import math

from lib.geometry_nodes.scatter import (
    PlacementStrategy,
    FurnitureCategory,
    FurnitureBounds,
    PlacementConstraint,
    FurnitureItem,
    PlacedItem,
    ScatterResult,
    FURNITURE_CATALOG,
    ROOM_FURNITURE_SETS,
    FurnitureScatterer,
    scatter_furniture,
)


class TestPlacementStrategy:
    """Tests for PlacementStrategy enum."""

    def test_placement_strategy_values(self):
        """Test that PlacementStrategy enum has expected values."""
        assert PlacementStrategy.GRID.value == "grid"
        assert PlacementStrategy.RANDOM.value == "random"
        assert PlacementStrategy.WALL_ALIGNED.value == "wall_aligned"
        assert PlacementStrategy.CENTERED.value == "centered"
        assert PlacementStrategy.CORNER.value == "corner"
        assert PlacementStrategy.ERGONOMIC.value == "ergonomic"

    def test_placement_strategy_count(self):
        """Test that all expected strategies exist."""
        assert len(PlacementStrategy) == 6


class TestFurnitureCategory:
    """Tests for FurnitureCategory enum."""

    def test_furniture_category_values(self):
        """Test that FurnitureCategory enum has expected values."""
        assert FurnitureCategory.SEATING.value == "seating"
        assert FurnitureCategory.TABLE.value == "table"
        assert FurnitureCategory.STORAGE.value == "storage"
        assert FurnitureCategory.BED.value == "bed"
        assert FurnitureCategory.DESK.value == "desk"
        assert FurnitureCategory.LIGHTING.value == "lighting"
        assert FurnitureCategory.DECORATION.value == "decoration"
        assert FurnitureCategory.APPLIANCE.value == "appliance"

    def test_furniture_category_count(self):
        """Test that all expected categories exist."""
        assert len(FurnitureCategory) == 8


class TestFurnitureBounds:
    """Tests for FurnitureBounds dataclass."""

    def test_default_values(self):
        """Test FurnitureBounds default values."""
        bounds = FurnitureBounds()
        assert bounds.width == 0.5
        assert bounds.depth == 0.5
        assert bounds.height == 0.5

    def test_custom_values(self):
        """Test FurnitureBounds with custom values."""
        bounds = FurnitureBounds(width=2.0, depth=1.0, height=0.8)
        assert bounds.width == 2.0
        assert bounds.depth == 1.0
        assert bounds.height == 0.8

    def test_footprint(self):
        """Test FurnitureBounds.footprint property."""
        bounds = FurnitureBounds(width=2.0, depth=1.5)
        assert bounds.footprint == pytest.approx(3.0, rel=0.01)

    def test_footprint_square(self):
        """Test footprint for square bounds."""
        bounds = FurnitureBounds(width=1.0, depth=1.0)
        assert bounds.footprint == pytest.approx(1.0, rel=0.01)

    def test_to_dict(self):
        """Test FurnitureBounds.to_dict() serialization."""
        bounds = FurnitureBounds(width=1.5, depth=0.8, height=0.9)
        data = bounds.to_dict()
        assert data["width"] == 1.5
        assert data["depth"] == 0.8
        assert data["height"] == 0.9


class TestPlacementConstraint:
    """Tests for PlacementConstraint dataclass."""

    def test_default_values(self):
        """Test PlacementConstraint default values."""
        constraint = PlacementConstraint()
        assert constraint.constraint_type == "avoid_wall"
        assert constraint.target == ""
        assert constraint.distance == 0.5
        assert constraint.weight == 1.0

    def test_custom_values(self):
        """Test PlacementConstraint with custom values."""
        constraint = PlacementConstraint(
            constraint_type="against_wall",
            target="north_wall",
            distance=0.0,
            weight=0.8,
        )
        assert constraint.constraint_type == "against_wall"
        assert constraint.target == "north_wall"
        assert constraint.weight == 0.8

    def test_to_dict(self):
        """Test PlacementConstraint.to_dict() serialization."""
        constraint = PlacementConstraint(
            constraint_type="distance_from",
            target="sofa",
            distance=1.0,
        )
        data = constraint.to_dict()
        assert data["constraint_type"] == "distance_from"
        assert data["distance"] == 1.0


class TestFurnitureItem:
    """Tests for FurnitureItem dataclass."""

    def test_default_values(self):
        """Test FurnitureItem default values."""
        item = FurnitureItem()
        assert item.item_id == ""
        assert item.name == ""
        assert item.category == "prop"
        assert item.bounds.width == 0.5
        assert item.model_path == ""
        assert item.placement_strategy == "random"
        assert item.constraints == []
        assert item.required_clearance == 0.1
        assert item.can_stack is False
        assert item.tags == []

    def test_custom_values(self):
        """Test FurnitureItem with custom values."""
        item = FurnitureItem(
            item_id="sofa_001",
            name="Modern Sofa",
            category="seating",
            bounds=FurnitureBounds(width=2.0, depth=1.0, height=0.8),
            placement_strategy="wall_aligned",
            required_clearance=0.5,
            tags=["living_room", "modern"],
        )
        assert item.item_id == "sofa_001"
        assert item.name == "Modern Sofa"
        assert item.bounds.width == 2.0
        assert "modern" in item.tags

    def test_to_dict(self):
        """Test FurnitureItem.to_dict() serialization."""
        item = FurnitureItem(
            item_id="chair_001",
            name="Dining Chair",
            bounds=FurnitureBounds(width=0.5, depth=0.5),
            constraints=[PlacementConstraint(constraint_type="grid")],
        )
        data = item.to_dict()
        assert data["item_id"] == "chair_001"
        assert len(data["constraints"]) == 1


class TestPlacedItem:
    """Tests for PlacedItem dataclass."""

    def test_default_values(self):
        """Test PlacedItem default values."""
        placed = PlacedItem()
        assert placed.instance_id == ""
        assert placed.item_id == ""
        assert placed.position == (0.0, 0.0, 0.0)
        assert placed.rotation == (0.0, 0.0, 0.0)
        assert placed.scale == 1.0
        assert placed.variant == 0

    def test_custom_values(self):
        """Test PlacedItem with custom values."""
        placed = PlacedItem(
            instance_id="inst_001",
            item_id="sofa_001",
            position=(5.0, 3.0, 0.0),
            rotation=(0.0, 0.0, 90.0),
            scale=1.2,
            variant=2,
        )
        assert placed.instance_id == "inst_001"
        assert placed.position == (5.0, 3.0, 0.0)
        assert placed.rotation == (0.0, 0.0, 90.0)

    def test_to_dict(self):
        """Test PlacedItem.to_dict() serialization."""
        placed = PlacedItem(
            instance_id="inst_001",
            item_id="sofa_001",
            position=(1.0, 2.0, 3.0),
        )
        data = placed.to_dict()
        assert data["instance_id"] == "inst_001"
        assert data["position"] == [1.0, 2.0, 3.0]


class TestScatterResult:
    """Tests for ScatterResult dataclass."""

    def test_default_values(self):
        """Test ScatterResult default values."""
        result = ScatterResult()
        assert result.success is True
        assert result.placed_items == []
        assert result.rejected_items == []
        assert result.coverage == 0.0
        assert result.collision_count == 0

    def test_custom_values(self):
        """Test ScatterResult with custom values."""
        result = ScatterResult(
            success=True,
            placed_items=[PlacedItem(instance_id="inst_001")],
            rejected_items=["item_001"],
            coverage=0.25,
            collision_count=10,
        )
        assert result.success is True
        assert len(result.placed_items) == 1
        assert len(result.rejected_items) == 1
        assert result.coverage == 0.25

    def test_to_dict(self):
        """Test ScatterResult.to_dict() serialization."""
        result = ScatterResult(
            placed_items=[PlacedItem(instance_id="inst_001")],
            rejected_items=["bad_item"],
        )
        data = result.to_dict()
        assert len(data["placed_items"]) == 1
        assert data["rejected_items"] == ["bad_item"]


class TestFurnitureCatalog:
    """Tests for FURNITURE_CATALOG dictionary."""

    def test_catalog_not_empty(self):
        """Test that catalog has items."""
        assert len(FURNITURE_CATALOG) > 0

    def test_sofa_2seat_exists(self):
        """Test that 2-seat sofa exists in catalog."""
        assert "sofa_2seat" in FURNITURE_CATALOG
        sofa = FURNITURE_CATALOG["sofa_2seat"]
        assert sofa.category == "seating"
        assert sofa.placement_strategy == "wall_aligned"

    def test_dining_table_exists(self):
        """Test that dining table exists in catalog."""
        assert "dining_table" in FURNITURE_CATALOG
        table = FURNITURE_CATALOG["dining_table"]
        assert table.category == "table"
        assert table.placement_strategy == "centered"

    def test_bed_double_exists(self):
        """Test that double bed exists in catalog."""
        assert "bed_double" in FURNITURE_CATALOG
        bed = FURNITURE_CATALOG["bed_double"]
        assert bed.category == "bed"

    def test_all_items_have_valid_bounds(self):
        """Test that all catalog items have valid bounds."""
        for item_id, item in FURNITURE_CATALOG.items():
            assert item.bounds.width > 0, f"{item_id} has invalid width"
            assert item.bounds.depth > 0, f"{item_id} has invalid depth"
            assert item.bounds.height > 0, f"{item_id} has invalid height"

    def test_all_items_have_tags(self):
        """Test that all catalog items have tags."""
        for item_id, item in FURNITURE_CATALOG.items():
            assert len(item.tags) > 0, f"{item_id} has no tags"


class TestRoomFurnitureSets:
    """Tests for ROOM_FURNITURE_SETS dictionary."""

    def test_living_room_exists(self):
        """Test that living room set exists."""
        assert "living_room" in ROOM_FURNITURE_SETS
        living = ROOM_FURNITURE_SETS["living_room"]
        assert "sofa_2seat" in living

    def test_bedroom_exists(self):
        """Test that bedroom set exists."""
        assert "bedroom" in ROOM_FURNITURE_SETS
        bedroom = ROOM_FURNITURE_SETS["bedroom"]
        assert "bed_double" in bedroom

    def test_office_exists(self):
        """Test that office set exists."""
        assert "office" in ROOM_FURNITURE_SETS
        office = ROOM_FURNITURE_SETS["office"]
        assert "desk" in office

    def test_dining_room_exists(self):
        """Test that dining room set exists."""
        assert "dining_room" in ROOM_FURNITURE_SETS

    def test_kitchen_exists(self):
        """Test that kitchen set exists."""
        assert "kitchen" in ROOM_FURNITURE_SETS

    def test_all_sets_reference_valid_items(self):
        """Test that all furniture sets reference items in catalog."""
        for room_type, items in ROOM_FURNITURE_SETS.items():
            for item_id in items:
                assert item_id in FURNITURE_CATALOG, f"{room_type} references unknown item {item_id}"


class TestFurnitureScatterer:
    """Tests for FurnitureScatterer class."""

    def test_default_initialization(self):
        """Test FurnitureScatterer default initialization."""
        scatterer = FurnitureScatterer()
        assert scatterer.catalog is not None
        assert scatterer._instance_counter == 0

    def test_initialization_with_seed(self):
        """Test FurnitureScatterer with seed for reproducibility."""
        scatterer1 = FurnitureScatterer(seed=42)
        scatterer2 = FurnitureScatterer(seed=42)

        # Both should produce same sequence
        pos1 = scatterer1._find_position(
            FurnitureItem(bounds=FurnitureBounds(width=0.5, depth=0.5)),
            (0.0, 0.0, 10.0, 10.0),
            []
        )
        pos2 = scatterer2._find_position(
            FurnitureItem(bounds=FurnitureBounds(width=0.5, depth=0.5)),
            (0.0, 0.0, 10.0, 10.0),
            []
        )
        assert pos1 == pos2

    def test_scatter_basic(self):
        """Test basic scatter operation."""
        scatterer = FurnitureScatterer(seed=42)
        result = scatterer.scatter(
            room_bounds=(0.0, 0.0, 10.0, 8.0),
            furniture_set="living_room",
        )

        assert result.success is True
        assert len(result.placed_items) > 0

    def test_scatter_unknown_set(self):
        """Test scatter with unknown furniture set."""
        scatterer = FurnitureScatterer()
        result = scatterer.scatter(
            room_bounds=(0.0, 0.0, 10.0, 8.0),
            furniture_set="nonexistent",
        )

        assert result.success is False
        assert len(result.rejected_items) > 0

    def test_scatter_with_density(self):
        """Test scatter with reduced density."""
        scatterer = FurnitureScatterer(seed=42)

        result_full = scatterer.scatter(
            room_bounds=(0.0, 0.0, 10.0, 8.0),
            furniture_set="living_room",
            density=1.0,
        )

        scatterer2 = FurnitureScatterer(seed=42)
        result_half = scatterer2.scatter(
            room_bounds=(0.0, 0.0, 10.0, 8.0),
            furniture_set="living_room",
            density=0.5,
        )

        assert len(result_full.placed_items) >= len(result_half.placed_items)

    def test_scatter_with_avoid_zones(self):
        """Test scatter with avoid zones."""
        scatterer = FurnitureScatterer(seed=42)
        result = scatterer.scatter(
            room_bounds=(0.0, 0.0, 10.0, 8.0),
            furniture_set="living_room",
            avoid_zones=[(4.0, 3.0, 6.0, 5.0)],  # Center zone
        )

        # Should still place items
        assert result.success is True

    def test_scatter_with_existing_items(self):
        """Test scatter with existing items."""
        scatterer = FurnitureScatterer(seed=42)
        existing = [
            PlacedItem(
                instance_id="existing_001",
                item_id="sofa_2seat",
                position=(2.0, 2.0, 0.0),
            )
        ]

        result = scatterer.scatter(
            room_bounds=(0.0, 0.0, 10.0, 8.0),
            furniture_set="living_room",
            existing_items=existing,
        )

        assert result.success is True

    def test_scatter_small_room(self):
        """Test scatter in very small room."""
        scatterer = FurnitureScatterer(seed=42)
        result = scatterer.scatter(
            room_bounds=(0.0, 0.0, 2.0, 2.0),
            furniture_set="living_room",
        )

        # Some items might be rejected due to space
        # but operation should complete
        assert isinstance(result.success, bool)

    def test_find_position_random(self):
        """Test finding position with random strategy."""
        scatterer = FurnitureScatterer(seed=42)
        item = FurnitureItem(
            item_id="test",
            placement_strategy="random",
            bounds=FurnitureBounds(width=0.5, depth=0.5),
        )

        position = scatterer._find_position(item, (0.0, 0.0, 10.0, 10.0), [])

        assert position is not None
        assert 0.0 < position[0] < 10.0
        assert 0.0 < position[1] < 10.0

    def test_find_position_centered(self):
        """Test finding position with centered strategy."""
        scatterer = FurnitureScatterer(seed=42)
        item = FurnitureItem(
            item_id="test",
            placement_strategy="centered",
            bounds=FurnitureBounds(width=0.5, depth=0.5),
        )

        position = scatterer._find_position(item, (0.0, 0.0, 10.0, 10.0), [])

        assert position is not None
        # Should be near center (5, 5)
        assert 4.0 < position[0] < 6.0
        assert 4.0 < position[1] < 6.0

    def test_find_position_corner(self):
        """Test finding position with corner strategy."""
        scatterer = FurnitureScatterer(seed=42)
        item = FurnitureItem(
            item_id="test",
            placement_strategy="corner",
            bounds=FurnitureBounds(width=0.5, depth=0.5),
        )

        position = scatterer._find_position(item, (0.0, 0.0, 10.0, 10.0), [])

        assert position is not None
        # Should be near one of the corners
        in_corner = (
            (position[0] < 2.0 and position[1] < 2.0) or  # Bottom-left
            (position[0] > 8.0 and position[1] < 2.0) or  # Bottom-right
            (position[0] < 2.0 and position[1] > 8.0) or  # Top-left
            (position[0] > 8.0 and position[1] > 8.0)     # Top-right
        )
        assert in_corner

    def test_find_position_wall_aligned(self):
        """Test finding position with wall_aligned strategy."""
        scatterer = FurnitureScatterer(seed=42)
        item = FurnitureItem(
            item_id="test",
            placement_strategy="wall_aligned",
            bounds=FurnitureBounds(width=0.5, depth=0.5),
        )

        position = scatterer._find_position(item, (0.0, 0.0, 10.0, 10.0), [])

        assert position is not None
        # Should be near one of the walls
        near_wall = (
            position[0] < 2.0 or  # Left wall
            position[0] > 8.0 or  # Right wall
            position[1] < 2.0 or  # Bottom wall
            position[1] > 8.0     # Top wall
        )
        assert near_wall

    def test_find_position_collision(self):
        """Test that collision detection works."""
        scatterer = FurnitureScatterer(seed=42)
        item = FurnitureItem(
            item_id="test",
            placement_strategy="random",
            bounds=FurnitureBounds(width=2.0, depth=2.0),
            required_clearance=0.5,
        )

        # Avoid zone covering most of the room
        avoid_zones = [(2.0, 2.0, 8.0, 8.0)]

        position = scatterer._find_position(item, (0.0, 0.0, 10.0, 10.0), avoid_zones)

        # Should either find a corner or return None
        if position is not None:
            # If found, should be in corner area
            assert (
                position[0] < 2.0 or position[0] > 8.0 or
                position[1] < 2.0 or position[1] > 8.0
            )

    def test_find_position_no_space(self):
        """Test finding position when no space available."""
        scatterer = FurnitureScatterer(seed=42)
        item = FurnitureItem(
            item_id="test",
            placement_strategy="random",
            bounds=FurnitureBounds(width=5.0, depth=5.0),
            required_clearance=1.0,
        )

        # Room too small for item
        position = scatterer._find_position(item, (0.0, 0.0, 4.0, 4.0), [])

        assert position is None

    def test_calculate_rotation_wall_aligned(self):
        """Test rotation calculation for wall-aligned items."""
        scatterer = FurnitureScatterer(seed=42)
        item = FurnitureItem(placement_strategy="wall_aligned")

        rotation = scatterer._calculate_rotation(item, (0.0, 5.0, 0.0), (0.0, 0.0, 10.0, 10.0))

        assert rotation[0] == 0.0
        assert rotation[1] == 0.0
        # Z rotation should face center

    def test_calculate_rotation_corner(self):
        """Test rotation calculation for corner items."""
        scatterer = FurnitureScatterer(seed=42)
        item = FurnitureItem(placement_strategy="corner")

        rotation = scatterer._calculate_rotation(item, (0.0, 0.0, 0.0), (0.0, 0.0, 10.0, 10.0))

        assert rotation[0] == 0.0
        assert rotation[1] == 0.0
        assert rotation[2] in [45.0, 135.0, 225.0, 315.0]

    def test_calculate_rotation_random(self):
        """Test rotation calculation for random items."""
        scatterer = FurnitureScatterer(seed=42)
        item = FurnitureItem(placement_strategy="random")

        rotation = scatterer._calculate_rotation(item, (5.0, 5.0, 0.0), (0.0, 0.0, 10.0, 10.0))

        assert rotation[0] == 0.0
        assert rotation[1] == 0.0
        assert 0.0 <= rotation[2] < 360.0

    def test_check_collision_no_collision(self):
        """Test collision check with no collision."""
        scatterer = FurnitureScatterer()
        bounds = (0.0, 0.0, 2.0, 2.0)
        avoid_zones = [(5.0, 5.0, 7.0, 7.0)]

        has_collision = scatterer._check_collision(bounds, avoid_zones)

        assert has_collision is False

    def test_check_collision_with_collision(self):
        """Test collision check with collision."""
        scatterer = FurnitureScatterer()
        bounds = (0.0, 0.0, 5.0, 5.0)
        avoid_zones = [(3.0, 3.0, 6.0, 6.0)]

        has_collision = scatterer._check_collision(bounds, avoid_zones)

        assert has_collision is True

    def test_bounds_overlap_overlapping(self):
        """Test bounds overlap check for overlapping bounds."""
        scatterer = FurnitureScatterer()
        a = (0.0, 0.0, 5.0, 5.0)
        b = (3.0, 3.0, 8.0, 8.0)

        assert scatterer._bounds_overlap(a, b) is True

    def test_bounds_overlap_non_overlapping(self):
        """Test bounds overlap check for non-overlapping bounds."""
        scatterer = FurnitureScatterer()
        a = (0.0, 0.0, 3.0, 3.0)
        b = (5.0, 5.0, 8.0, 8.0)

        assert scatterer._bounds_overlap(a, b) is False

    def test_generate_instance_id(self):
        """Test instance ID generation."""
        scatterer = FurnitureScatterer()

        id1 = scatterer._generate_instance_id()
        id2 = scatterer._generate_instance_id()
        id3 = scatterer._generate_instance_id()

        assert id1 != id2
        assert id2 != id3
        assert id1.startswith("furniture_")

    def test_coverage_calculation(self):
        """Test coverage calculation."""
        scatterer = FurnitureScatterer(seed=42)
        result = scatterer.scatter(
            room_bounds=(0.0, 0.0, 10.0, 10.0),  # 100 sq m
            furniture_set="living_room",
        )

        assert result.coverage >= 0.0
        assert result.coverage < 1.0  # Should not fill entire room


class TestScatterFurniture:
    """Tests for scatter_furniture convenience function."""

    def test_scatter_furniture_basic(self):
        """Test basic scatter function."""
        result = scatter_furniture(
            room_bounds=(0.0, 0.0, 10.0, 8.0),
            room_type="living_room",
        )

        assert result.success is True
        assert len(result.placed_items) > 0

    def test_scatter_furniture_with_seed(self):
        """Test scatter function with seed."""
        result1 = scatter_furniture(
            room_bounds=(0.0, 0.0, 10.0, 8.0),
            room_type="office",
            seed=42,
        )
        result2 = scatter_furniture(
            room_bounds=(0.0, 0.0, 10.0, 8.0),
            room_type="office",
            seed=42,
        )

        assert len(result1.placed_items) == len(result2.placed_items)


class TestFurnitureScattererEdgeCases:
    """Edge case tests for FurnitureScatterer."""

    def test_scatter_empty_room(self):
        """Test scatter with zero-size room."""
        scatterer = FurnitureScatterer()
        result = scatterer.scatter(
            room_bounds=(0.0, 0.0, 0.0, 0.0),
            furniture_set="living_room",
        )

        assert result.success is False

    def test_scatter_item_not_in_catalog(self):
        """Test scatter when furniture set references non-catalog item."""
        scatterer = FurnitureScatterer()

        # Create a modified furniture set with invalid item
        # This is internal testing - we'll check via rejected_items
        scatterer.catalog = {}  # Empty catalog

        result = scatterer.scatter(
            room_bounds=(0.0, 0.0, 10.0, 10.0),
            furniture_set="living_room",
        )

        assert result.success is False

    def test_scatter_high_density(self):
        """Test scatter with density > 1.0."""
        scatterer = FurnitureScatterer(seed=42)
        result = scatterer.scatter(
            room_bounds=(0.0, 0.0, 10.0, 10.0),
            furniture_set="living_room",
            density=2.0,  # Should still work but capped at available items
        )

        # Should still work
        assert isinstance(result.success, bool)

    def test_existing_item_collision(self):
        """Test that existing items block placement."""
        scatterer = FurnitureScatterer(seed=42)

        # Place a large item in center
        existing = [
            PlacedItem(
                instance_id="blocker",
                item_id="dining_table",  # Large item
                position=(5.0, 5.0, 0.0),
            )
        ]

        result = scatterer.scatter(
            room_bounds=(0.0, 0.0, 10.0, 10.0),
            furniture_set="living_room",
            existing_items=existing,
        )

        # Should still place items in other areas
        assert result.success is True

    def test_multiple_scatters_same_scatterer(self):
        """Test multiple scatter operations with same scatterer."""
        scatterer = FurnitureScatterer(seed=42)

        result1 = scatterer.scatter(
            room_bounds=(0.0, 0.0, 5.0, 5.0),
            furniture_set="office",
        )

        result2 = scatterer.scatter(
            room_bounds=(0.0, 0.0, 5.0, 5.0),
            furniture_set="bedroom",
        )

        assert result1.success is True
        assert result2.success is True

        # Instance IDs should be unique across both
        all_ids = [p.instance_id for p in result1.placed_items + result2.placed_items]
        assert len(all_ids) == len(set(all_ids))
