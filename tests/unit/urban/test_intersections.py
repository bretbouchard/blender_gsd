"""
Tests for Intersection Builder

Tests intersection geometry generation.
"""

import pytest
from lib.urban.intersections import (
    IntersectionShape,
    IntersectionConfig,
    IntersectionGeometry,
    IntersectionBuilder,
    create_intersection_geometry,
)
from lib.urban.types import RoadNetwork, RoadNode


class TestIntersectionShape:
    """Tests for IntersectionShape enum."""

    def test_shape_values(self):
        """Test IntersectionShape enum values."""
        assert IntersectionShape.SQUARE.value == "square"
        assert IntersectionShape.CIRCULAR.value == "circular"
        assert IntersectionShape.OCTAGONAL.value == "octagonal"
        assert IntersectionShape.CUSTOM.value == "custom"


class TestIntersectionConfig:
    """Tests for IntersectionConfig dataclass."""

    def test_create_default(self):
        """Test creating IntersectionConfig with defaults."""
        config = IntersectionConfig()
        assert config.intersection_type == "four_way"
        assert config.radius == 8.0
        assert config.has_crosswalks is True
        assert config.has_traffic_signals is False

    def test_create_with_values(self):
        """Test creating IntersectionConfig with values."""
        config = IntersectionConfig(
            intersection_type="roundabout",
            radius=15.0,
            has_crosswalks=True,
            has_traffic_signals=False,
            has_stop_signs=True,
            crosswalk_width=4.0,
            island_radius=10.0,
        )
        assert config.intersection_type == "roundabout"
        assert config.radius == 15.0
        assert config.has_stop_signs is True

    def test_to_dict(self):
        """Test IntersectionConfig serialization."""
        config = IntersectionConfig(
            intersection_type="three_way_t",
            radius=6.0,
        )
        result = config.to_dict()
        assert result["intersection_type"] == "three_way_t"
        assert result["radius"] == 6.0


class TestIntersectionGeometry:
    """Tests for IntersectionGeometry dataclass."""

    def test_create_default(self):
        """Test creating IntersectionGeometry with defaults."""
        geometry = IntersectionGeometry()
        assert geometry.node_id == ""
        assert geometry.position == (0.0, 0.0, 0.0)
        assert geometry.crosswalk_positions == []
        assert geometry.signal_positions == []

    def test_create_with_values(self):
        """Test creating IntersectionGeometry with values."""
        config = IntersectionConfig(intersection_type="four_way")
        geometry = IntersectionGeometry(
            node_id="int_01",
            position=(100.0, 100.0, 0.0),
            config=config,
            crosswalk_positions=[(0, 0, 0, 0)],
            signal_positions=[(10, 10, 0, 45)],
        )
        assert geometry.node_id == "int_01"
        assert geometry.position == (100.0, 100.0, 0.0)
        assert len(geometry.crosswalk_positions) == 1

    def test_to_dict(self):
        """Test IntersectionGeometry serialization."""
        geometry = IntersectionGeometry(
            node_id="test",
            position=(0, 0, 0),
        )
        result = geometry.to_dict()
        assert result["node_id"] == "test"
        assert result["position"] == [0, 0, 0]


class TestIntersectionBuilder:
    """Tests for IntersectionBuilder class."""

    def test_init(self):
        """Test IntersectionBuilder initialization."""
        builder = IntersectionBuilder()
        assert builder.default_radius == 8.0

    def test_init_with_radius(self):
        """Test initialization with custom radius."""
        builder = IntersectionBuilder(default_radius=10.0)
        assert builder.default_radius == 10.0

    def test_build_from_network_empty(self):
        """Test building from empty network."""
        builder = IntersectionBuilder()
        network = RoadNetwork()
        intersections = builder.build_from_network(network)
        assert len(intersections) == 0

    def test_build_from_network_with_4way(self):
        """Test building from network with 4-way intersection."""
        builder = IntersectionBuilder()
        network = RoadNetwork()
        network.nodes = [
            RoadNode(
                id="int_01",
                position=(100, 100),
                node_type="intersection_4way",
                has_crosswalk=True,
                has_traffic_light=True,
            ),
        ]
        intersections = builder.build_from_network(network)
        assert len(intersections) == 1
        assert intersections[0].config.has_traffic_signals is True

    def test_build_from_network_with_3way(self):
        """Test building from network with 3-way intersection."""
        builder = IntersectionBuilder()
        network = RoadNetwork()
        network.nodes = [
            RoadNode(
                id="int_01",
                position=(50, 50),
                node_type="intersection_3way",
            ),
        ]
        intersections = builder.build_from_network(network)
        assert len(intersections) == 1
        assert intersections[0].config.intersection_type == "intersection_3way"

    def test_build_from_network_with_roundabout(self):
        """Test building from network with roundabout."""
        builder = IntersectionBuilder()
        network = RoadNetwork()
        network.nodes = [
            RoadNode(
                id="rabout_01",
                position=(0, 0),
                node_type="roundabout",
            ),
        ]
        intersections = builder.build_from_network(network)
        assert len(intersections) == 1
        assert intersections[0].config.intersection_type == "roundabout"

    def test_build_from_network_filters_non_intersections(self):
        """Test that non-intersection nodes are filtered."""
        builder = IntersectionBuilder()
        network = RoadNetwork()
        network.nodes = [
            RoadNode(id="n1", position=(0, 0), node_type="dead_end"),
            RoadNode(id="n2", position=(10, 0), node_type="curve_point"),
            RoadNode(id="n3", position=(20, 0), node_type="intersection_4way"),
        ]
        intersections = builder.build_from_network(network)
        assert len(intersections) == 1
        assert intersections[0].node_id == "n3"


class TestCreateIntersectionGeometry:
    """Tests for create_intersection_geometry function."""

    def test_create_from_empty_network(self):
        """Test creating from empty network."""
        network = RoadNetwork()
        intersections = create_intersection_geometry(network)
        assert len(intersections) == 0

    def test_create_from_network(self):
        """Test creating from network."""
        network = RoadNetwork()
        network.nodes = [
            RoadNode(
                id="int_01",
                position=(0, 0),
                node_type="intersection_4way",
            ),
        ]
        intersections = create_intersection_geometry(network)
        assert len(intersections) == 1


class TestIntersectionCrosswalks:
    """Tests for crosswalk positioning."""

    def test_four_way_crosswalks(self):
        """Test 4-way intersection has 4 crosswalks."""
        builder = IntersectionBuilder()
        network = RoadNetwork()
        network.nodes = [
            RoadNode(
                id="int_01",
                position=(0, 0),
                node_type="intersection_4way",
                has_crosswalk=True,
            ),
        ]
        intersections = builder.build_from_network(network)
        # 4-way should have 4 crosswalks
        assert len(intersections[0].crosswalk_positions) == 4

    def test_three_way_crosswalks(self):
        """Test 3-way intersection has 3 crosswalks."""
        builder = IntersectionBuilder()
        network = RoadNetwork()
        network.nodes = [
            RoadNode(
                id="int_01",
                position=(0, 0),
                node_type="intersection_3way",
                has_crosswalk=True,
            ),
        ]
        intersections = builder.build_from_network(network)
        # 3-way should have 3 crosswalks
        assert len(intersections[0].crosswalk_positions) == 3

    def test_no_crosswalks_when_disabled(self):
        """Test no crosswalks when disabled."""
        builder = IntersectionBuilder()
        network = RoadNetwork()
        network.nodes = [
            RoadNode(
                id="int_01",
                position=(0, 0),
                node_type="intersection_4way",
                has_crosswalk=False,
            ),
        ]
        intersections = builder.build_from_network(network)
        assert len(intersections[0].crosswalk_positions) == 0


class TestIntersectionSignals:
    """Tests for traffic signal positioning."""

    def test_four_way_signals(self):
        """Test 4-way intersection has 4 signals."""
        builder = IntersectionBuilder()
        network = RoadNetwork()
        network.nodes = [
            RoadNode(
                id="int_01",
                position=(0, 0),
                node_type="intersection_4way",
                has_traffic_light=True,
            ),
        ]
        intersections = builder.build_from_network(network)
        # 4-way should have 4 signal positions
        assert len(intersections[0].signal_positions) == 4

    def test_no_signals_when_disabled(self):
        """Test no signals when disabled."""
        builder = IntersectionBuilder()
        network = RoadNetwork()
        network.nodes = [
            RoadNode(
                id="int_01",
                position=(0, 0),
                node_type="intersection_4way",
                has_traffic_light=False,
            ),
        ]
        intersections = builder.build_from_network(network)
        assert len(intersections[0].signal_positions) == 0


class TestIntersectionEdgeCases:
    """Edge case tests for intersections."""

    def test_roundabout_island_radius(self):
        """Test roundabout island radius is set."""
        builder = IntersectionBuilder()
        network = RoadNetwork()
        network.nodes = [
            RoadNode(
                id="rabout",
                position=(0, 0),
                node_type="roundabout",
            ),
        ]
        intersections = builder.build_from_network(network)
        assert intersections[0].config.island_radius > 0

    def test_elevated_intersection(self):
        """Test intersection with elevation."""
        builder = IntersectionBuilder()
        network = RoadNetwork()
        network.nodes = [
            RoadNode(
                id="elevated",
                position=(0, 0),
                node_type="intersection_4way",
                elevation=5.0,
            ),
        ]
        intersections = builder.build_from_network(network)
        assert intersections[0].position[2] == 5.0
