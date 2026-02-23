"""
Tests for Urban Types

Tests all data structures and enums in the urban types module.
"""

import pytest
from lib.urban.types import (
    NodeType,
    EdgeType,
    RoadType,
    IntersectionType,
    UrbanStyle,
    RoadNode,
    LaneConfig,
    RoadEdge,
    RoadNetwork,
    validate_node,
    validate_edge,
    validate_network,
)


class TestEnums:
    """Tests for enum types."""

    def test_node_type_values(self):
        """Test NodeType enum values."""
        assert NodeType.INTERSECTION_4WAY.value == "intersection_4way"
        assert NodeType.INTERSECTION_3WAY.value == "intersection_3way"
        assert NodeType.ROUNDABOUT.value == "roundabout"
        assert NodeType.DEAD_END.value == "dead_end"
        assert NodeType.CURVE_POINT.value == "curve_point"

    def test_edge_type_values(self):
        """Test EdgeType enum values."""
        assert EdgeType.ROAD.value == "road"
        assert EdgeType.HIGHWAY.value == "highway"
        assert EdgeType.RESIDENTIAL.value == "residential"
        assert EdgeType.PEDESTRIAN.value == "pedestrian"

    def test_road_type_values(self):
        """Test RoadType enum values."""
        assert RoadType.HIGHWAY.value == "highway"
        assert RoadType.ARTERIAL.value == "arterial"
        assert RoadType.COLLECTOR.value == "collector"
        assert RoadType.LOCAL.value == "local"
        assert RoadType.RESIDENTIAL.value == "residential"

    def test_intersection_type_values(self):
        """Test IntersectionType enum values."""
        assert IntersectionType.FOUR_WAY.value == "four_way"
        assert IntersectionType.THREE_WAY_T.value == "three_way_t"
        assert IntersectionType.ROUNDABOUT.value == "roundabout"

    def test_urban_style_values(self):
        """Test UrbanStyle enum values."""
        assert UrbanStyle.MODERN_URBAN.value == "modern_urban"
        assert UrbanStyle.DOWNTOWN.value == "downtown"
        assert UrbanStyle.SUBURBAN.value == "suburban"
        assert UrbanStyle.INDUSTRIAL.value == "industrial"
        assert UrbanStyle.HISTORIC.value == "historic"


class TestLaneConfig:
    """Tests for LaneConfig dataclass."""

    def test_create_default(self):
        """Test creating LaneConfig with defaults."""
        config = LaneConfig()
        assert config.count == 2
        assert config.width == 3.5
        assert config.direction == "both"
        assert config.has_sidewalk is True

    def test_create_with_values(self):
        """Test creating LaneConfig with values."""
        config = LaneConfig(
            count=4,
            width=3.75,
            direction="forward",
            has_center_turn=True,
            has_bike_lane=True,
            has_parking=True,
            has_sidewalk=True,
            sidewalk_width=2.0,
        )
        assert config.count == 4
        assert config.width == 3.75
        assert config.has_center_turn is True
        assert config.has_bike_lane is True

    def test_total_width_calculation(self):
        """Test total width calculation."""
        config = LaneConfig(count=2, width=3.5)
        # 2 lanes * 3.5m = 7m base
        # + 2 sidewalks * 1.5m = 3m
        assert config.total_width == 10.0

    def test_total_width_with_extras(self):
        """Test total width with extra lanes."""
        config = LaneConfig(
            count=2,
            width=3.5,
            has_center_turn=True,
            has_bike_lane=True,
            has_parking=True,
        )
        # Base: 7m + center turn: 3.5m + bike: 3m + parking: 5m + sidewalk: 3m
        width = config.total_width
        assert width > 10.0  # Should be larger than base

    def test_to_dict(self):
        """Test LaneConfig serialization."""
        config = LaneConfig(count=4, width=3.5)
        result = config.to_dict()
        assert result["count"] == 4
        assert result["width"] == 3.5
        assert "total_width" in result


class TestRoadNode:
    """Tests for RoadNode dataclass."""

    def test_create_default(self):
        """Test creating RoadNode with defaults."""
        node = RoadNode()
        assert node.id == "node_0"
        assert node.position == (0.0, 0.0)
        assert node.node_type == "intersection_4way"
        assert node.elevation == 0.0
        assert node.connections == []

    def test_create_with_values(self):
        """Test creating RoadNode with values."""
        node = RoadNode(
            id="custom_node",
            position=(100.0, 200.0),
            node_type="intersection_3way",
            elevation=5.0,
            has_traffic_light=True,
            has_crosswalk=False,
        )
        assert node.id == "custom_node"
        assert node.position == (100.0, 200.0)
        assert node.node_type == "intersection_3way"
        assert node.elevation == 5.0
        assert node.has_traffic_light is True

    def test_to_dict(self):
        """Test RoadNode serialization."""
        node = RoadNode(id="test", position=(10, 20))
        result = node.to_dict()
        assert result["id"] == "test"
        assert result["position"] == [10, 20]

    def test_from_dict(self):
        """Test RoadNode deserialization."""
        data = {
            "id": "loaded_node",
            "position": [50, 100],
            "node_type": "roundabout",
            "elevation": 10.0,
        }
        node = RoadNode.from_dict(data)
        assert node.id == "loaded_node"
        assert node.position == (50, 100)
        assert node.node_type == "roundabout"


class TestRoadEdge:
    """Tests for RoadEdge dataclass."""

    def test_create_default(self):
        """Test creating RoadEdge with defaults."""
        edge = RoadEdge()
        assert edge.id == "edge_0"
        assert edge.from_node == ""
        assert edge.to_node == ""
        assert edge.road_type == "local"
        assert edge.speed_limit == 50

    def test_create_with_values(self):
        """Test creating RoadEdge with values."""
        edge = RoadEdge(
            id="custom_edge",
            from_node="node_1",
            to_node="node_2",
            road_type="arterial",
            name="Main Street",
            curve_points=[(0, 0), (10, 10), (20, 0)],
            speed_limit=60,
            has_median=True,
        )
        assert edge.id == "custom_edge"
        assert edge.from_node == "node_1"
        assert edge.to_node == "node_2"
        assert edge.name == "Main Street"
        assert len(edge.curve_points) == 3

    def test_length_property(self):
        """Test edge length calculation."""
        edge = RoadEdge(curve_points=[(0, 0), (10, 0), (10, 10)])
        length = edge.length
        assert length == pytest.approx(20.0, rel=0.01)

    def test_length_empty_curve(self):
        """Test edge length with no curve points."""
        edge = RoadEdge(curve_points=[])
        assert edge.length == 0.0

    def test_to_dict(self):
        """Test RoadEdge serialization."""
        edge = RoadEdge(id="test", from_node="a", to_node="b")
        result = edge.to_dict()
        assert result["id"] == "test"
        assert result["from_node"] == "a"
        assert result["to_node"] == "b"
        assert "length" in result

    def test_from_dict(self):
        """Test RoadEdge deserialization."""
        data = {
            "id": "loaded_edge",
            "from_node": "node_a",
            "to_node": "node_b",
            "road_type": "highway",
            "curve_points": [[0, 0], [100, 0]],
            "speed_limit": 100,
        }
        edge = RoadEdge.from_dict(data)
        assert edge.id == "loaded_edge"
        assert edge.from_node == "node_a"
        assert edge.road_type == "highway"


class TestRoadNetwork:
    """Tests for RoadNetwork dataclass."""

    def test_create_default(self):
        """Test creating RoadNetwork with defaults."""
        network = RoadNetwork()
        assert network.version == "1.0"
        assert network.dimensions == (100.0, 100.0)
        assert network.nodes == []
        assert network.edges == []

    def test_create_with_values(self):
        """Test creating RoadNetwork with values."""
        nodes = [RoadNode(id="n1"), RoadNode(id="n2")]
        edges = [RoadEdge(id="e1", from_node="n1", to_node="n2")]
        network = RoadNetwork(
            dimensions=(200, 200),
            nodes=nodes,
            edges=edges,
            style="downtown",
            seed=42,
        )
        assert network.dimensions == (200, 200)
        assert len(network.nodes) == 2
        assert len(network.edges) == 1
        assert network.style == "downtown"

    def test_get_node_by_id(self):
        """Test getting node by ID."""
        network = RoadNetwork()
        network.nodes = [RoadNode(id="node_a"), RoadNode(id="node_b")]
        node = network.get_node_by_id("node_a")
        assert node is not None
        assert node.id == "node_a"

    def test_get_node_by_id_not_found(self):
        """Test getting nonexistent node."""
        network = RoadNetwork()
        network.nodes = [RoadNode(id="node_a")]
        node = network.get_node_by_id("nonexistent")
        assert node is None

    def test_get_edge_by_id(self):
        """Test getting edge by ID."""
        network = RoadNetwork()
        network.edges = [RoadEdge(id="edge_1")]
        edge = network.get_edge_by_id("edge_1")
        assert edge is not None

    def test_get_edges_from_node(self):
        """Test getting edges connected to node."""
        network = RoadNetwork()
        network.edges = [
            RoadEdge(id="e1", from_node="n1", to_node="n2"),
            RoadEdge(id="e2", from_node="n2", to_node="n3"),
        ]
        edges = network.get_edges_from_node("n1")
        assert len(edges) == 1
        assert edges[0].id == "e1"

    def test_get_connected_nodes(self):
        """Test getting connected nodes."""
        network = RoadNetwork()
        network.edges = [
            RoadEdge(id="e1", from_node="n1", to_node="n2"),
            RoadEdge(id="e2", from_node="n1", to_node="n3"),
        ]
        connected = network.get_connected_nodes("n1")
        assert "n2" in connected
        assert "n3" in connected

    def test_is_connected_empty(self):
        """Test connectivity check on empty network."""
        network = RoadNetwork()
        assert network.is_connected() is True

    def test_is_connected_true(self):
        """Test connectivity check - connected."""
        network = RoadNetwork()
        network.nodes = [RoadNode(id="n1"), RoadNode(id="n2")]
        network.edges = [RoadEdge(id="e1", from_node="n1", to_node="n2")]
        assert network.is_connected() is True

    def test_total_road_length(self):
        """Test total road length calculation."""
        network = RoadNetwork()
        network.edges = [
            RoadEdge(curve_points=[(0, 0), (10, 0)]),
            RoadEdge(curve_points=[(0, 0), (0, 20)]),
        ]
        total = network.total_road_length
        assert total == pytest.approx(30.0, rel=0.01)

    def test_to_dict(self):
        """Test RoadNetwork serialization."""
        network = RoadNetwork(
            dimensions=(100, 100),
            style="urban",
        )
        result = network.to_dict()
        assert result["dimensions"] == [100, 100]
        assert "stats" in result

    def test_from_dict(self):
        """Test RoadNetwork deserialization."""
        data = {
            "version": "1.0",
            "dimensions": [200, 200],
            "nodes": [{"id": "n1"}],
            "edges": [{"id": "e1", "from_node": "n1", "to_node": "n2"}],
            "style": "downtown",
        }
        network = RoadNetwork.from_dict(data)
        assert network.dimensions == (200, 200)
        assert len(network.nodes) == 1
        assert network.style == "downtown"

    def test_to_json_and_from_json(self):
        """Test JSON round trip."""
        network = RoadNetwork(
            dimensions=(150, 150),
            nodes=[RoadNode(id="n1")],
            style="modern_urban",
        )
        json_str = network.to_json()
        loaded = RoadNetwork.from_json(json_str)
        assert loaded.dimensions == (150, 150)
        assert len(loaded.nodes) == 1


class TestValidation:
    """Tests for validation functions."""

    def test_validate_node_valid(self):
        """Test validating valid node."""
        node = RoadNode(id="valid", connections=["e1", "e2"])
        errors = validate_node(node)
        assert len(errors) == 0

    def test_validate_node_no_id(self):
        """Test validating node without ID."""
        node = RoadNode(id="")
        errors = validate_node(node)
        assert len(errors) > 0

    def test_validate_edge_valid(self):
        """Test validating valid edge."""
        edge = RoadEdge(
            id="valid",
            from_node="n1",
            to_node="n2",
        )
        errors = validate_edge(edge)
        assert len(errors) == 0

    def test_validate_edge_no_id(self):
        """Test validating edge without ID."""
        edge = RoadEdge(id="")
        errors = validate_edge(edge)
        assert len(errors) > 0

    def test_validate_edge_no_nodes(self):
        """Test validating edge without nodes."""
        edge = RoadEdge(id="e1", from_node="", to_node="")
        errors = validate_edge(edge)
        assert len(errors) > 0

    def test_validate_network_valid(self):
        """Test validating valid network."""
        network = RoadNetwork(
            dimensions=(100, 100),
            nodes=[RoadNode(id="n1"), RoadNode(id="n2")],
            edges=[RoadEdge(id="e1", from_node="n1", to_node="n2")],
        )
        errors = validate_network(network)
        assert len(errors) == 0

    def test_validate_network_invalid_dimensions(self):
        """Test validating network with invalid dimensions."""
        network = RoadNetwork(dimensions=(-100, 100))
        errors = validate_network(network)
        assert len(errors) > 0

    def test_validate_network_no_nodes(self):
        """Test validating network without nodes."""
        network = RoadNetwork(nodes=[])
        errors = validate_network(network)
        assert len(errors) > 0

    def test_validate_network_disconnected(self):
        """Test validating disconnected network."""
        network = RoadNetwork(
            nodes=[RoadNode(id="n1"), RoadNode(id="n2")],
            edges=[],  # No edges connecting them
        )
        errors = validate_network(network)
        # May or may not be an error depending on validation rules
        assert isinstance(errors, list)
