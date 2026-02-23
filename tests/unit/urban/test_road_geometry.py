"""
Tests for Road Geometry Builder

Tests road segment and geometry generation.
"""

import pytest
from lib.urban.road_geometry import (
    RoadSurfaceType,
    LaneConfig,
    RoadSegment,
    RoadGeometry,
    RoadGeometryBuilder,
    create_road_geometry_from_network,
)
from lib.urban.types import RoadNetwork, RoadNode, RoadEdge, LaneConfig as TypesLaneConfig


class TestRoadSurfaceType:
    """Tests for RoadSurfaceType enum."""

    def test_surface_type_values(self):
        """Test RoadSurfaceType enum values."""
        assert RoadSurfaceType.ASPHALT.value == "asphalt"
        assert RoadSurfaceType.CONCRETE.value == "concrete"
        assert RoadSurfaceType.COBBLESTONE.value == "cobblestone"
        assert RoadSurfaceType.GRAVEL.value == "gravel"
        assert RoadSurfaceType.DIRT.value == "dirt"
        assert RoadSurfaceType.BRICK.value == "brick"


class TestLaneConfigModule:
    """Tests for LaneConfig in road_geometry module."""

    def test_create_default(self):
        """Test creating LaneConfig with defaults."""
        config = LaneConfig()
        assert config.count == 2
        assert config.width == 3.5
        assert config.has_center_line is True

    def test_create_with_values(self):
        """Test creating LaneConfig with values."""
        config = LaneConfig(
            count=4,
            width=3.75,
            has_center_line=True,
            has_edge_lines=True,
            has_lane_markings=True,
        )
        assert config.count == 4
        assert config.has_lane_markings is True


class TestRoadSegment:
    """Tests for RoadSegment dataclass."""

    def test_create_default(self):
        """Test creating RoadSegment with defaults."""
        segment = RoadSegment()
        assert segment.edge_id == ""
        assert segment.start_pos == (0.0, 0.0, 0.0)
        assert segment.end_pos == (1.0, 0.0, 0.0)
        assert segment.width == 10.0
        assert segment.has_curb is True

    def test_create_with_values(self):
        """Test creating RoadSegment with values."""
        segment = RoadSegment(
            edge_id="edge_01",
            start_pos=(0.0, 0.0, 0.0),
            end_pos=(100.0, 0.0, 0.0),
            width=12.0,
            has_curb=True,
            curb_height=0.2,
            surface_type="concrete",
        )
        assert segment.edge_id == "edge_01"
        assert segment.end_pos == (100.0, 0.0, 0.0)
        assert segment.width == 12.0

    def test_length_property(self):
        """Test segment length calculation."""
        segment = RoadSegment(
            start_pos=(0.0, 0.0, 0.0),
            end_pos=(50.0, 0.0, 0.0),
        )
        assert segment.length == 50.0

    def test_length_with_curve_points(self):
        """Test segment length with curve points."""
        segment = RoadSegment(
            start_pos=(0.0, 0.0, 0.0),
            end_pos=(20.0, 0.0, 0.0),
            control_points=[(10.0, 5.0, 0.0), (10.0, -5.0, 0.0)],
        )
        # Curved path should be longer than straight line
        assert segment.length > 20.0

    def test_direction_property(self):
        """Test segment direction calculation."""
        import math
        segment = RoadSegment(
            start_pos=(0.0, 0.0, 0.0),
            end_pos=(10.0, 10.0, 0.0),
        )
        # 45 degrees (pi/4 radians)
        assert segment.direction == pytest.approx(math.pi / 4, rel=0.01)

    def test_to_dict(self):
        """Test RoadSegment serialization."""
        segment = RoadSegment(
            edge_id="test",
            start_pos=(0, 0, 0),
            end_pos=(10, 0, 0),
        )
        result = segment.to_dict()
        assert result["edge_id"] == "test"
        assert "length" in result
        assert "direction" in result


class TestRoadGeometry:
    """Tests for RoadGeometry dataclass."""

    def test_create_default(self):
        """Test creating RoadGeometry with defaults."""
        geometry = RoadGeometry()
        assert geometry.segments == []
        assert geometry.total_length == 0.0
        assert geometry.total_area == 0.0

    def test_create_with_segments(self):
        """Test creating RoadGeometry with segments."""
        segment = RoadSegment(
            start_pos=(0, 0, 0),
            end_pos=(100, 0, 0),
            width=10.0,
        )
        geometry = RoadGeometry(
            segments=[segment],
            total_length=100.0,
            total_area=1000.0,
        )
        assert len(geometry.segments) == 1
        assert geometry.total_length == 100.0

    def test_to_dict(self):
        """Test RoadGeometry serialization."""
        geometry = RoadGeometry()
        result = geometry.to_dict()
        assert "segments" in result
        assert "total_length" in result
        assert "segment_count" in result


class TestRoadGeometryBuilder:
    """Tests for RoadGeometryBuilder class."""

    def test_init(self):
        """Test RoadGeometryBuilder initialization."""
        builder = RoadGeometryBuilder()
        assert builder.default_width == 10.0
        assert builder.default_curb_height == 0.15

    def test_init_with_values(self):
        """Test initialization with values."""
        builder = RoadGeometryBuilder(
            default_width=12.0,
            default_curb_height=0.2,
            default_sidewalk_width=2.0,
        )
        assert builder.default_width == 12.0
        assert builder.default_curb_height == 0.2

    def test_build_from_network_empty(self):
        """Test building from empty network."""
        builder = RoadGeometryBuilder()
        network = RoadNetwork()
        geometry = builder.build_from_network(network)
        assert len(geometry.segments) == 0

    def test_build_from_network_with_edges(self):
        """Test building from network with edges."""
        builder = RoadGeometryBuilder()
        network = RoadNetwork()
        network.nodes = [
            RoadNode(id="n1", position=(0, 0)),
            RoadNode(id="n2", position=(100, 0)),
        ]
        network.edges = [
            RoadEdge(
                id="e1",
                from_node="n1",
                to_node="n2",
                curve_points=[(0, 0), (100, 0)],
            ),
        ]
        geometry = builder.build_from_network(network)
        assert len(geometry.segments) == 1
        assert geometry.total_length > 0

    def test_build_from_network_with_multiple_edges(self):
        """Test building from network with multiple edges."""
        builder = RoadGeometryBuilder()
        network = RoadNetwork()
        network.nodes = [
            RoadNode(id="n1", position=(0, 0)),
            RoadNode(id="n2", position=(100, 0)),
            RoadNode(id="n3", position=(100, 100)),
        ]
        network.edges = [
            RoadEdge(
                id="e1",
                from_node="n1",
                to_node="n2",
                curve_points=[(0, 0), (100, 0)],
            ),
            RoadEdge(
                id="e2",
                from_node="n2",
                to_node="n3",
                curve_points=[(100, 0), (100, 100)],
            ),
        ]
        geometry = builder.build_from_network(network)
        assert len(geometry.segments) == 2


class TestCreateRoadGeometryFromNetwork:
    """Tests for create_road_geometry_from_network function."""

    def test_create_from_empty_network(self):
        """Test creating from empty network."""
        network = RoadNetwork()
        geometry = create_road_geometry_from_network(network)
        assert len(geometry.segments) == 0

    def test_create_from_network(self):
        """Test creating from network."""
        network = RoadNetwork()
        network.nodes = [
            RoadNode(id="n1", position=(0, 0)),
            RoadNode(id="n2", position=(50, 0)),
        ]
        network.edges = [
            RoadEdge(
                id="e1",
                from_node="n1",
                to_node="n2",
                curve_points=[(0, 0), (50, 0)],
            ),
        ]
        geometry = create_road_geometry_from_network(network)
        assert len(geometry.segments) == 1


class TestRoadGeometryEdgeCases:
    """Edge case tests for road geometry."""

    def test_segment_with_elevation(self):
        """Test segment with elevation change."""
        segment = RoadSegment(
            start_pos=(0, 0, 0),
            end_pos=(10, 0, 5),
        )
        # With control points, length is calculated differently
        # Without control points, only 2D length is calculated (ignoring z)
        assert segment.length == 10.0

    def test_segment_with_elevation_and_curve_points(self):
        """Test segment with elevation and curve points."""
        segment = RoadSegment(
            start_pos=(0, 0, 0),
            end_pos=(10, 0, 5),
            control_points=[(5, 0, 2.5)],
        )
        # With control points, 3D length is calculated
        assert segment.length > 10.0

    def test_segment_zero_length(self):
        """Test segment with zero length."""
        segment = RoadSegment(
            start_pos=(0, 0, 0),
            end_pos=(0, 0, 0),
        )
        assert segment.length == 0.0

    def test_very_wide_segment(self):
        """Test very wide segment."""
        segment = RoadSegment(width=50.0)
        assert segment.width == 50.0

    def test_network_with_missing_nodes(self):
        """Test network with edges referencing missing nodes."""
        builder = RoadGeometryBuilder()
        network = RoadNetwork()
        network.nodes = [RoadNode(id="n1", position=(0, 0))]
        network.edges = [
            RoadEdge(
                id="e1",
                from_node="n1",
                to_node="nonexistent",
                curve_points=[(0, 0), (100, 0)],
            ),
        ]
        geometry = builder.build_from_network(network)
        # Should handle gracefully - segment not created for missing node
        assert isinstance(geometry, RoadGeometry)
        assert len(geometry.segments) == 0

    def test_segment_with_lane_config(self):
        """Test segment with lane configuration."""
        lane_config = LaneConfig(count=4, width=3.5)
        segment = RoadSegment(
            edge_id="test",
            lane_config=lane_config,
        )
        assert segment.lane_config is not None
        assert segment.lane_config.count == 4

    def test_segment_surface_type(self):
        """Test segment surface type."""
        segment = RoadSegment(surface_type="cobblestone")
        assert segment.surface_type == "cobblestone"

    def test_network_with_elevation(self):
        """Test network with node elevation."""
        builder = RoadGeometryBuilder()
        network = RoadNetwork()
        network.nodes = [
            RoadNode(id="n1", position=(0, 0), elevation=0.0),
            RoadNode(id="n2", position=(100, 0), elevation=5.0),
        ]
        network.edges = [
            RoadEdge(
                id="e1",
                from_node="n1",
                to_node="n2",
                curve_points=[(0, 0), (100, 0)],
            ),
        ]
        geometry = builder.build_from_network(network)
        assert len(geometry.segments) == 1
        # Check that elevation is preserved
        assert geometry.segments[0].start_pos[2] == 0.0
        assert geometry.segments[0].end_pos[2] == 5.0

    def test_geometry_total_area(self):
        """Test geometry total area calculation."""
        builder = RoadGeometryBuilder()
        network = RoadNetwork()
        network.nodes = [
            RoadNode(id="n1", position=(0, 0)),
            RoadNode(id="n2", position=(100, 0)),
        ]
        network.edges = [
            RoadEdge(
                id="e1",
                from_node="n1",
                to_node="n2",
                curve_points=[(0, 0), (100, 0)],
            ),
        ]
        geometry = builder.build_from_network(network)
        # Total area should be length * width
        assert geometry.total_area > 0
        assert geometry.total_area == geometry.total_length * geometry.segments[0].width
