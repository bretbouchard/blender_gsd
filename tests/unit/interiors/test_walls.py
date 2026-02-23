"""
Tests for Wall Builder

Tests wall geometry generation from floor plans.
"""

import pytest
from lib.interiors.walls import (
    WallType,
    WallOpening,
    WallSegment,
    WallGeometry,
    WallBuilder,
    create_wall_geometry_from_plan,
)
from lib.interiors.types import FloorPlan, Room, DoorSpec, WindowSpec


class TestWallType:
    """Tests for WallType enum."""

    def test_wall_type_values(self):
        """Test WallType enum values."""
        assert WallType.EXTERIOR.value == "exterior"
        assert WallType.INTERIOR.value == "interior"
        assert WallType.PARTITION.value == "partition"
        assert WallType.LOAD_BEARING.value == "load_bearing"


class TestWallOpening:
    """Tests for WallOpening dataclass."""

    def test_create_default(self):
        """Test creating WallOpening with defaults."""
        opening = WallOpening()
        assert opening.opening_type == "door"
        assert opening.position == 0.5
        assert opening.width == 0.9
        assert opening.height == 2.1

    def test_create_with_values(self):
        """Test creating WallOpening with values."""
        opening = WallOpening(
            opening_type="window",
            position=0.3,
            width=1.5,
            height=1.2,
            sill_height=0.9,
            header_height=2.1,
        )
        assert opening.opening_type == "window"
        assert opening.sill_height == 0.9

    def test_to_dict(self):
        """Test WallOpening serialization."""
        opening = WallOpening(opening_type="window", width=1.2)
        result = opening.to_dict()
        assert result["opening_type"] == "window"
        assert result["width"] == 1.2


class TestWallSegment:
    """Tests for WallSegment dataclass."""

    def test_create_default(self):
        """Test creating WallSegment with defaults."""
        segment = WallSegment()
        assert segment.start == (0.0, 0.0)
        assert segment.end == (1.0, 0.0)
        assert segment.height == 2.8
        assert segment.thickness == 0.15

    def test_create_with_values(self):
        """Test creating WallSegment with values."""
        segment = WallSegment(
            start=(0, 0),
            end=(5, 0),
            height=3.0,
            thickness=0.2,
            wall_type="exterior",
            material="brick_red",
        )
        assert segment.end == (5, 0)
        assert segment.wall_type == "exterior"

    def test_length_property(self):
        """Test wall length calculation."""
        segment = WallSegment(start=(0, 0), end=(5, 0))
        assert segment.length == 5.0

        segment = WallSegment(start=(0, 0), end=(3, 4))
        assert segment.length == 5.0

    def test_angle_property(self):
        """Test wall angle calculation."""
        segment = WallSegment(start=(0, 0), end=(1, 0))
        assert segment.angle == 0.0

        segment = WallSegment(start=(0, 0), end=(0, 1))
        import math
        assert segment.angle == math.pi / 2

    def test_center_property(self):
        """Test wall center calculation."""
        segment = WallSegment(start=(0, 0), end=(4, 2))
        assert segment.center == (2.0, 1.0)

    def test_get_point_at_position(self):
        """Test point calculation at position."""
        segment = WallSegment(start=(0, 0), end=(10, 0))

        assert segment.get_point_at_position(0.0) == (0, 0)
        assert segment.get_point_at_position(0.5) == (5, 0)
        assert segment.get_point_at_position(1.0) == (10, 0)

    def test_to_dict(self):
        """Test WallSegment serialization."""
        segment = WallSegment(start=(0, 0), end=(5, 0))
        result = segment.to_dict()
        assert result["start"] == [0, 0]
        assert result["length"] == 5.0


class TestWallGeometry:
    """Tests for WallGeometry dataclass."""

    def test_create_default(self):
        """Test creating WallGeometry with defaults."""
        geometry = WallGeometry()
        assert geometry.segments == []
        assert geometry.total_length == 0.0

    def test_create_with_segments(self):
        """Test creating WallGeometry with segments."""
        segments = [
            WallSegment(start=(0, 0), end=(5, 0)),
            WallSegment(start=(5, 0), end=(5, 4)),
        ]
        geometry = WallGeometry(segments=segments)
        assert len(geometry.segments) == 2

    def test_to_dict(self):
        """Test WallGeometry serialization."""
        geometry = WallGeometry(
            segments=[WallSegment(start=(0, 0), end=(5, 0))],
            total_length=5.0,
        )
        result = geometry.to_dict()
        assert result["total_length"] == 5.0
        assert result["segment_count"] == 1


class TestWallBuilder:
    """Tests for WallBuilder class."""

    def test_init(self):
        """Test WallBuilder initialization."""
        builder = WallBuilder()
        assert builder.default_height == 2.8
        assert builder.default_thickness == 0.15

    def test_init_with_params(self):
        """Test WallBuilder initialization with parameters."""
        builder = WallBuilder(
            default_height=3.0,
            default_thickness=0.2,
            exterior_thickness=0.3,
        )
        assert builder.default_height == 3.0
        assert builder.exterior_thickness == 0.3

    def test_build_from_plan_empty(self):
        """Test building from empty plan."""
        builder = WallBuilder()
        plan = FloorPlan()
        geometry = builder.build_from_plan(plan)

        assert len(geometry.segments) == 0

    def test_build_from_plan_single_room(self):
        """Test building from plan with single room."""
        builder = WallBuilder()
        room = Room(
            id="r1",
            polygon=[(0, 0), (5, 0), (5, 4), (0, 4)],
        )
        plan = FloorPlan(dimensions=(5, 4), rooms=[room])
        geometry = builder.build_from_plan(plan)

        assert len(geometry.segments) == 4  # 4 walls
        assert geometry.total_length > 0

    def test_build_from_plan_with_doors(self):
        """Test building walls with door openings."""
        builder = WallBuilder()
        room = Room(
            id="r1",
            polygon=[(0, 0), (5, 0), (5, 4), (0, 4)],
            doors=[DoorSpec(wall_index=0, position=0.5, width=1.0)],
        )
        plan = FloorPlan(dimensions=(5, 4), rooms=[room])
        geometry = builder.build_from_plan(plan)

        # Check that door opening was added
        segment_with_door = None
        for segment in geometry.segments:
            if segment.openings:
                segment_with_door = segment
                break

        assert segment_with_door is not None
        assert len(segment_with_door.openings) == 1

    def test_build_from_plan_with_windows(self):
        """Test building walls with window openings."""
        builder = WallBuilder()
        room = Room(
            id="r1",
            polygon=[(0, 0), (5, 0), (5, 4), (0, 4)],
            windows=[WindowSpec(wall_index=0, position=0.5, width=1.2)],
        )
        plan = FloorPlan(dimensions=(5, 4), rooms=[room])
        geometry = builder.build_from_plan(plan)

        # Check that window opening was added
        segment_with_window = None
        for segment in geometry.segments:
            for opening in segment.openings:
                if opening.opening_type == "window":
                    segment_with_window = segment
                    break

        assert segment_with_window is not None

    def test_exterior_wall_detection(self):
        """Test detection of exterior walls."""
        builder = WallBuilder()
        room = Room(
            id="r1",
            polygon=[(0, 0), (5, 0), (5, 4), (0, 4)],
        )
        plan = FloorPlan(dimensions=(5, 4), rooms=[room])
        geometry = builder.build_from_plan(plan)

        # All walls should be exterior (room fills entire plan)
        exterior_count = sum(1 for s in geometry.segments if s.wall_type == "exterior")
        assert exterior_count == 4

    def test_interior_wall_detection(self):
        """Test detection of interior walls."""
        builder = WallBuilder()
        room = Room(
            id="r1",
            polygon=[(1, 1), (4, 1), (4, 3), (1, 3)],  # Room inside plan
        )
        plan = FloorPlan(dimensions=(5, 4), rooms=[room])
        geometry = builder.build_from_plan(plan)

        # All walls should be interior (room is inside plan)
        interior_count = sum(1 for s in geometry.segments if s.wall_type == "interior")
        assert interior_count == 4

    def test_calculate_totals(self):
        """Test calculation of total lengths."""
        builder = WallBuilder()
        room = Room(
            id="r1",
            polygon=[(0, 0), (5, 0), (5, 4), (0, 4)],
        )
        plan = FloorPlan(dimensions=(5, 4), rooms=[room])
        geometry = builder.build_from_plan(plan)

        assert geometry.total_length == 18.0  # 2*(5+4)
        assert geometry.exterior_length > 0


class TestCreateWallGeometryFromPlan:
    """Tests for create_wall_geometry_from_plan function."""

    def test_create(self):
        """Test creating wall geometry from plan."""
        room = Room(
            id="r1",
            polygon=[(0, 0), (5, 0), (5, 4), (0, 4)],
        )
        plan = FloorPlan(dimensions=(5, 4), rooms=[room])
        geometry = create_wall_geometry_from_plan(plan)

        assert len(geometry.segments) == 4


class TestWallBuilderEdgeCases:
    """Edge case tests for wall builder."""

    def test_small_room(self):
        """Test building walls for small room."""
        builder = WallBuilder()
        room = Room(
            id="r1",
            polygon=[(0, 0), (1, 0), (1, 1), (0, 1)],
        )
        plan = FloorPlan(dimensions=(1, 1), rooms=[room])
        geometry = builder.build_from_plan(plan)

        assert len(geometry.segments) == 4

    def test_multiple_rooms(self):
        """Test building walls for multiple rooms."""
        builder = WallBuilder()
        room1 = Room(id="r1", polygon=[(0, 0), (5, 0), (5, 4), (0, 4)])
        room2 = Room(id="r2", polygon=[(5, 0), (10, 0), (10, 4), (5, 4)])
        plan = FloorPlan(dimensions=(10, 4), rooms=[room1, room2])
        geometry = builder.build_from_plan(plan)

        # Should have 6 unique walls (shared wall deduplication)
        assert len(geometry.segments) == 6

    def test_room_with_no_polygon(self):
        """Test handling room with empty polygon."""
        builder = WallBuilder()
        room = Room(id="r1", polygon=[])
        plan = FloorPlan(rooms=[room])
        geometry = builder.build_from_plan(plan)

        assert len(geometry.segments) == 0

    def test_room_with_two_points(self):
        """Test handling room with only two points."""
        builder = WallBuilder()
        room = Room(id="r1", polygon=[(0, 0), (5, 0)])
        plan = FloorPlan(rooms=[room])
        geometry = builder.build_from_plan(plan)

        assert len(geometry.segments) == 0
