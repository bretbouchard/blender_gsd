"""
Tests for Road Markings System

Tests marking specs, catalogs, and placement.
"""

import pytest
from lib.urban.markings import (
    MarkingColor,
    MarkingType,
    MarkingMaterial,
    MarkingSpec,
    MarkingInstance,
    CrosswalkGeometry,
    LANE_LINE_MARKINGS,
    CROSSWALK_MARKINGS,
    SYMBOL_MARKINGS,
    MARKING_CATALOG,
    MarkingPlacer,
    create_marking_placer,
)


class TestEnums:
    """Tests for enum types."""

    def test_marking_color_values(self):
        """Test MarkingColor enum values."""
        assert MarkingColor.WHITE.value == "white"
        assert MarkingColor.YELLOW.value == "yellow"
        assert MarkingColor.RED.value == "red"
        assert MarkingColor.BLUE.value == "blue"

    def test_marking_type_values(self):
        """Test MarkingType enum values."""
        assert MarkingType.SOLID_LINE.value == "solid_line"
        assert MarkingType.BROKEN_LINE.value == "broken_line"
        assert MarkingType.STANDARD_CROSSWALK.value == "standard_crosswalk"
        assert MarkingType.STOP_BAR.value == "stop_bar"
        assert MarkingType.STRAIGHT_ARROW.value == "straight_arrow"

    def test_marking_material_values(self):
        """Test MarkingMaterial enum values."""
        assert MarkingMaterial.PAINT.value == "paint"
        assert MarkingMaterial.THERMOPLASTIC.value == "thermoplastic"
        assert MarkingMaterial.EPOXY.value == "epoxy"


class TestMarkingSpec:
    """Tests for MarkingSpec dataclass."""

    def test_create_default(self):
        """Test creating MarkingSpec with defaults."""
        spec = MarkingSpec()
        assert spec.marking_id == ""
        assert spec.marking_type == "solid_line"
        assert spec.color == "white"
        assert spec.width == 0.15

    def test_create_with_values(self):
        """Test creating MarkingSpec with values."""
        spec = MarkingSpec(
            marking_id="solid_white",
            marking_type="solid_line",
            color="white",
            width=0.15,
            material="thermoplastic",
        )
        assert spec.marking_id == "solid_white"
        assert spec.color == "white"
        assert spec.material == "thermoplastic"

    def test_to_dict(self):
        """Test MarkingSpec serialization."""
        spec = MarkingSpec(marking_id="test", marking_type="solid_line")
        result = spec.to_dict()
        assert result["marking_id"] == "test"


class TestMarkingInstance:
    """Tests for MarkingInstance dataclass."""

    def test_create_default(self):
        """Test creating MarkingInstance with defaults."""
        instance = MarkingInstance()
        assert instance.instance_id == ""
        assert instance.start == (0.0, 0.0)
        assert instance.end == (1.0, 0.0)
        assert instance.rotation == 0.0

    def test_create_with_values(self):
        """Test creating MarkingInstance with values."""
        spec = MarkingSpec(marking_id="solid_white")
        instance = MarkingInstance(
            instance_id="marking_01",
            spec=spec,
            start=(0.0, 0.0),
            end=(10.0, 5.0),
            rotation=90.0,
        )
        assert instance.instance_id == "marking_01"
        assert instance.start == (0.0, 0.0)
        assert instance.end == (10.0, 5.0)

    def test_to_dict(self):
        """Test MarkingInstance serialization."""
        instance = MarkingInstance(instance_id="test")
        result = instance.to_dict()
        assert result["instance_id"] == "test"


class TestCrosswalkGeometry:
    """Tests for CrosswalkGeometry dataclass."""

    def test_create_default(self):
        """Test creating CrosswalkGeometry with defaults."""
        geom = CrosswalkGeometry()
        assert geom.marking_type == "CW-CONTINENTAL"
        assert geom.width == 3.0
        assert geom.length == 6.0
        assert geom.stripes == []

    def test_create_with_values(self):
        """Test creating CrosswalkGeometry with values."""
        geom = CrosswalkGeometry(
            marking_type="CW-ZEBRA",
            width=4.0,
            length=8.0,
            direction=45.0,
        )
        assert geom.marking_type == "CW-ZEBRA"
        assert geom.width == 4.0
        assert geom.length == 8.0

    def test_to_dict(self):
        """Test CrosswalkGeometry serialization."""
        geom = CrosswalkGeometry(marking_type="CW-LADDER")
        result = geom.to_dict()
        assert result["marking_type"] == "CW-LADDER"


class TestMarkingCatalogs:
    """Tests for marking catalogs."""

    def test_lane_line_markings_exist(self):
        """Test that LANE_LINE_MARKINGS is populated."""
        assert isinstance(LANE_LINE_MARKINGS, dict)
        assert len(LANE_LINE_MARKINGS) > 0

    def test_crosswalk_markings_exist(self):
        """Test that CROSSWALK_MARKINGS is populated."""
        assert isinstance(CROSSWALK_MARKINGS, dict)
        assert len(CROSSWALK_MARKINGS) > 0

    def test_symbol_markings_exist(self):
        """Test that SYMBOL_MARKINGS is populated."""
        assert isinstance(SYMBOL_MARKINGS, dict)
        assert len(SYMBOL_MARKINGS) > 0

    def test_marking_catalog_exists(self):
        """Test that MARKING_CATALOG is populated."""
        assert isinstance(MARKING_CATALOG, dict)
        assert len(MARKING_CATALOG) > 0


class TestMarkingPlacer:
    """Tests for MarkingPlacer class."""

    def test_init(self):
        """Test MarkingPlacer initialization."""
        placer = MarkingPlacer()
        assert placer is not None

    def test_place_lane_markings(self):
        """Test placing lane markings."""
        placer = MarkingPlacer()
        # place_lane_markings expects list of (start, end) tuples
        road_segments = [((0, 0), (100, 0))]
        markings = placer.place_lane_markings(
            road_segments=road_segments,
            lane_count=2,
            lane_width=3.5,
        )
        assert isinstance(markings, list)

    def test_place_lane_markings_multiple_segments(self):
        """Test placing lane markings on multiple segments."""
        placer = MarkingPlacer()
        road_segments = [((0, 0), (50, 0)), ((50, 0), (100, 0))]
        markings = placer.place_lane_markings(
            road_segments=road_segments,
            lane_count=2,
        )
        assert isinstance(markings, list)

    def test_place_crosswalk(self):
        """Test placing crosswalk."""
        placer = MarkingPlacer()
        crosswalk = placer.place_crosswalk(
            position=(50, 0, 0),
            direction=0.0,
            width=4.0,
            length=6.0,
        )
        assert crosswalk is not None
        assert isinstance(crosswalk, CrosswalkGeometry)

    def test_place_crosswalks_at_intersection(self):
        """Test placing crosswalks at intersection."""
        placer = MarkingPlacer()
        crosswalks = placer.place_crosswalks_at_intersection(
            position=(0, 0, 0),
            intersection_type="4way",
            road_width=10.0,
        )
        assert len(crosswalks) == 4

    def test_place_stop_bars(self):
        """Test placing stop bars."""
        placer = MarkingPlacer()
        stop_bars = placer.place_stop_bars(
            intersection_position=(0, 0, 0),
            approach_angles=[0, 90, 180, 270],
        )
        assert len(stop_bars) == 4

    def test_place_lane_arrows(self):
        """Test placing lane arrows."""
        placer = MarkingPlacer()
        # place_lane_arrows expects list of (x, y) points forming a centerline
        lane_centerline = [(0, 0), (50, 0), (100, 0)]
        arrows = placer.place_lane_arrows(
            lane_centerline=lane_centerline,
            arrow_type="ARROW-STRAIGHT",
            spacing=30.0,
        )
        assert len(arrows) > 0


class TestCreateMarkingPlacer:
    """Tests for create_marking_placer function."""

    def test_create(self):
        """Test creating marking placer."""
        placer = create_marking_placer()
        assert isinstance(placer, MarkingPlacer)


class TestMarkingEdgeCases:
    """Edge case tests for markings."""

    def test_very_long_road(self):
        """Test markings on very long road."""
        placer = MarkingPlacer()
        road_segments = [((0, 0), (1000, 0))]
        markings = placer.place_lane_markings(
            road_segments=road_segments,
        )
        assert len(markings) > 0

    def test_curved_road_markings(self):
        """Test markings on curved road."""
        placer = MarkingPlacer()
        # Multiple segments simulating a curve
        road_segments = [
            ((0, 0), (50, 0)),
            ((50, 0), (100, 25)),
        ]
        markings = placer.place_lane_markings(road_segments=road_segments)
        assert len(markings) > 0

    def test_crosswalk_different_styles(self):
        """Test crosswalk with different styles."""
        placer = MarkingPlacer()
        for style in ["CW-ZEBRA", "CW-CONTINENTAL", "CW-LADDER", "CW-STANDARD"]:
            crosswalk = placer.place_crosswalk(
                position=(0, 0, 0),
                direction=0.0,
                marking_type=style,
            )
            assert crosswalk is not None
            assert crosswalk.marking_type == style

    def test_crosswalk_at_roundabout(self):
        """Test placing crosswalks at roundabout."""
        placer = MarkingPlacer()
        crosswalks = placer.place_crosswalks_at_intersection(
            position=(0, 0, 0),
            intersection_type="roundabout",
        )
        assert len(crosswalks) == 4

    def test_crosswalk_at_3way(self):
        """Test placing crosswalks at 3-way intersection."""
        placer = MarkingPlacer()
        crosswalks = placer.place_crosswalks_at_intersection(
            position=(0, 0, 0),
            intersection_type="3way",
        )
        assert len(crosswalks) == 3
