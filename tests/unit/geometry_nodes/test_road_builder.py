"""
Unit tests for lib/geometry_nodes/road_builder.py

Tests the road builder system including:
- RoadType enum
- LaneType enum
- IntersectionType enum
- LaneSpec dataclass
- RoadSegment dataclass
- IntersectionGeometry dataclass
- RoadNetwork dataclass
- ROAD_TEMPLATES
- SURFACE_MATERIALS
- RoadBuilder class
- RoadBuilderGN class
- build_road_network function
- network_to_gn_format function
"""

import pytest
import json

from lib.geometry_nodes.road_builder import (
    RoadType,
    LaneType,
    IntersectionType,
    LaneSpec,
    RoadSegment,
    IntersectionGeometry,
    RoadNetwork,
    ROAD_TEMPLATES,
    SURFACE_MATERIALS,
    RoadBuilder,
    RoadBuilderGN,
    build_road_network,
    network_to_gn_format,
)


class TestRoadType:
    """Tests for RoadType enum."""

    def test_road_type_values(self):
        """Test that RoadType enum has expected values."""
        assert RoadType.HIGHWAY.value == "highway"
        assert RoadType.ARTERIAL.value == "arterial"
        assert RoadType.COLLECTOR.value == "collector"
        assert RoadType.LOCAL.value == "local"
        assert RoadType.RESIDENTIAL.value == "residential"
        assert RoadType.ALLEY.value == "alley"

    def test_road_type_count(self):
        """Test that all expected road types exist."""
        assert len(RoadType) == 6


class TestLaneType:
    """Tests for LaneType enum."""

    def test_lane_type_values(self):
        """Test that LaneType enum has expected values."""
        assert LaneType.TRAVEL.value == "travel"
        assert LaneType.TURN.value == "turn"
        assert LaneType.BIKE.value == "bike"
        assert LaneType.BUS.value == "bus"
        assert LaneType.PARKING.value == "parking"
        assert LaneType.EMERGENCY.value == "emergency"

    def test_lane_type_count(self):
        """Test that all expected lane types exist."""
        assert len(LaneType) == 6


class TestIntersectionType:
    """Tests for IntersectionType enum."""

    def test_intersection_type_values(self):
        """Test that IntersectionType enum has expected values."""
        assert IntersectionType.FOUR_WAY.value == "4way"
        assert IntersectionType.THREE_WAY_T.value == "3way_t"
        assert IntersectionType.THREE_WAY_Y.value == "3way_y"
        assert IntersectionType.ROUNDABOUT.value == "roundabout"
        assert IntersectionType.OVERPASS.value == "overpass"

    def test_intersection_type_count(self):
        """Test that all expected intersection types exist."""
        assert len(IntersectionType) == 5


class TestLaneSpec:
    """Tests for LaneSpec dataclass."""

    def test_default_values(self):
        """Test LaneSpec default values."""
        lane = LaneSpec()
        assert lane.lane_id == ""
        assert lane.lane_type == "travel"
        assert lane.width == 3.5
        assert lane.direction == 1
        assert lane.marking == "solid_white"

    def test_custom_values(self):
        """Test LaneSpec with custom values."""
        lane = LaneSpec(
            lane_id="lane_001",
            lane_type="bike",
            width=2.0,
            direction=-1,
            marking="dashed",
        )
        assert lane.lane_id == "lane_001"
        assert lane.lane_type == "bike"
        assert lane.width == 2.0

    def test_to_dict(self):
        """Test LaneSpec.to_dict() serialization."""
        lane = LaneSpec(lane_id="lane_001", width=4.0)
        data = lane.to_dict()
        assert data["lane_id"] == "lane_001"
        assert data["width"] == 4.0


class TestRoadSegment:
    """Tests for RoadSegment dataclass."""

    def test_default_values(self):
        """Test RoadSegment default values."""
        segment = RoadSegment()
        assert segment.segment_id == ""
        assert segment.start_node == ""
        assert segment.end_node == ""
        assert segment.road_type == "local"
        assert segment.speed_limit == 50.0
        assert segment.has_sidewalk is True
        assert segment.has_median is False

    def test_custom_values(self):
        """Test RoadSegment with custom values."""
        segment = RoadSegment(
            segment_id="seg_001",
            start_node="node_a",
            end_node="node_b",
            control_points=[(0.0, 0.0), (50.0, 0.0)],
            road_type="highway",
            speed_limit=120.0,
            has_sidewalk=False,
            has_median=True,
        )
        assert segment.segment_id == "seg_001"
        assert segment.road_type == "highway"
        assert len(segment.control_points) == 2

    def test_total_width(self):
        """Test RoadSegment.total_width property."""
        segment = RoadSegment(
            lanes=[
                LaneSpec(width=3.5),
                LaneSpec(width=3.5),
                LaneSpec(width=2.0),
            ]
        )
        assert segment.total_width == pytest.approx(9.0, rel=0.01)

    def test_total_width_empty(self):
        """Test total_width with no lanes."""
        segment = RoadSegment()
        assert segment.total_width == 0.0

    def test_lane_count(self):
        """Test RoadSegment.lane_count property."""
        segment = RoadSegment(
            lanes=[LaneSpec(), LaneSpec(), LaneSpec()]
        )
        assert segment.lane_count == 3

    def test_to_dict(self):
        """Test RoadSegment.to_dict() serialization."""
        segment = RoadSegment(
            segment_id="seg_001",
            control_points=[(0.0, 0.0), (10.0, 5.0)],
            lanes=[LaneSpec(lane_id="lane_001")],
        )
        data = segment.to_dict()
        assert data["segment_id"] == "seg_001"
        assert data["control_points"] == [[0.0, 0.0], [10.0, 5.0]]
        assert len(data["lanes"]) == 1


class TestIntersectionGeometry:
    """Tests for IntersectionGeometry dataclass."""

    def test_default_values(self):
        """Test IntersectionGeometry default values."""
        intersection = IntersectionGeometry()
        assert intersection.intersection_id == ""
        assert intersection.position == (0.0, 0.0)
        assert intersection.intersection_type == "4way"
        assert intersection.radius == 10.0
        assert intersection.signalized is False

    def test_custom_values(self):
        """Test IntersectionGeometry with custom values."""
        intersection = IntersectionGeometry(
            intersection_id="int_001",
            position=(100.0, 50.0),
            intersection_type="roundabout",
            radius=15.0,
            legs=["seg_001", "seg_002", "seg_003"],
            signalized=True,
        )
        assert intersection.intersection_id == "int_001"
        assert intersection.position == (100.0, 50.0)
        assert intersection.intersection_type == "roundabout"
        assert len(intersection.legs) == 3

    def test_to_dict(self):
        """Test IntersectionGeometry.to_dict() serialization."""
        intersection = IntersectionGeometry(
            intersection_id="int_001",
            position=(10.0, 20.0),
        )
        data = intersection.to_dict()
        assert data["intersection_id"] == "int_001"
        assert data["position"] == [10.0, 20.0]


class TestRoadNetwork:
    """Tests for RoadNetwork dataclass."""

    def test_default_values(self):
        """Test RoadNetwork default values."""
        network = RoadNetwork()
        assert network.network_id == ""
        assert network.segments == []
        assert network.intersections == []
        assert network.bounds == (0.0, 0.0, 100.0, 100.0)

    def test_custom_values(self):
        """Test RoadNetwork with custom values."""
        network = RoadNetwork(
            network_id="network_001",
            segments=[RoadSegment(segment_id="seg_001")],
            intersections=[IntersectionGeometry(intersection_id="int_001")],
            bounds=(0.0, 0.0, 200.0, 150.0),
        )
        assert network.network_id == "network_001"
        assert len(network.segments) == 1
        assert len(network.intersections) == 1

    def test_to_dict(self):
        """Test RoadNetwork.to_dict() serialization."""
        network = RoadNetwork(
            network_id="net_001",
            segments=[RoadSegment(segment_id="seg_001")],
            intersections=[IntersectionGeometry(intersection_id="int_001")],
        )
        data = network.to_dict()
        assert data["network_id"] == "net_001"
        assert len(data["segments"]) == 1
        assert len(data["intersections"]) == 1


class TestRoadTemplates:
    """Tests for ROAD_TEMPLATES dictionary."""

    def test_highway_exists(self):
        """Test that highway template exists."""
        assert "highway" in ROAD_TEMPLATES
        template = ROAD_TEMPLATES["highway"]
        assert template["speed_limit"] == 120
        assert template["has_median"] is True

    def test_local_exists(self):
        """Test that local template exists."""
        assert "local" in ROAD_TEMPLATES
        template = ROAD_TEMPLATES["local"]
        assert template["speed_limit"] == 40

    def test_all_templates_have_lanes(self):
        """Test that all templates have lanes defined."""
        for name, template in ROAD_TEMPLATES.items():
            assert "lanes" in template
            assert len(template["lanes"]) > 0

    def test_all_templates_have_required_keys(self):
        """Test that all templates have required keys."""
        required_keys = ["lanes", "speed_limit", "has_sidewalk", "has_median", "surface"]
        for name, template in ROAD_TEMPLATES.items():
            for key in required_keys:
                assert key in template, f"Template {name} missing key {key}"


class TestSurfaceMaterials:
    """Tests for SURFACE_MATERIALS dictionary."""

    def test_asphalt_exists(self):
        """Test that asphalt material exists."""
        assert "asphalt" in SURFACE_MATERIALS
        mat = SURFACE_MATERIALS["asphalt"]
        assert "color" in mat
        assert "roughness" in mat

    def test_concrete_exists(self):
        """Test that concrete material exists."""
        assert "concrete" in SURFACE_MATERIALS

    def test_all_materials_have_color(self):
        """Test that all materials have color defined."""
        for name, mat in SURFACE_MATERIALS.items():
            assert "color" in mat, f"Material {name} missing color"

    def test_all_materials_have_roughness(self):
        """Test that all materials have roughness defined."""
        for name, mat in SURFACE_MATERIALS.items():
            assert "roughness" in mat, f"Material {name} missing roughness"


class TestRoadBuilder:
    """Tests for RoadBuilder class."""

    def test_default_initialization(self):
        """Test RoadBuilder default initialization."""
        builder = RoadBuilder()
        assert builder.default_lane_width == 3.5
        assert builder.curb_height == 0.15
        assert builder.sidewalk_width == 1.5

    def test_custom_initialization(self):
        """Test RoadBuilder with custom parameters."""
        builder = RoadBuilder(
            default_lane_width=4.0,
            curb_height=0.2,
            sidewalk_width=2.0,
        )
        assert builder.default_lane_width == 4.0
        assert builder.curb_height == 0.2
        assert builder.sidewalk_width == 2.0

    def test_build_from_dict_empty(self):
        """Test building from empty dictionary."""
        builder = RoadBuilder()
        network = builder.build_from_dict({})

        assert network is not None
        assert len(network.segments) == 0
        assert len(network.intersections) == 0

    def test_build_from_dict_with_edges(self):
        """Test building from dictionary with edges."""
        builder = RoadBuilder()
        data = {
            "network_id": "test_network",
            "edges": [
                {
                    "id": "seg_001",
                    "from": "node_a",
                    "to": "node_b",
                    "road_type": "local",
                    "curve": [[0.0, 0.0], [50.0, 0.0]],
                }
            ],
        }

        network = builder.build_from_dict(data)

        assert network.network_id == "test_network"
        assert len(network.segments) == 1
        assert network.segments[0].segment_id == "seg_001"

    def test_build_from_dict_with_intersections(self):
        """Test building from dictionary with intersections."""
        builder = RoadBuilder()
        data = {
            "nodes": [
                {
                    "id": "int_001",
                    "type": "intersection_4way",
                    "position": [50.0, 50.0],
                },
                {
                    "id": "node_002",
                    "type": "regular",
                    "position": [100.0, 100.0],
                },
            ]
        }

        network = builder.build_from_dict(data)

        assert len(network.intersections) == 1
        assert network.intersections[0].intersection_id == "int_001"

    def test_build_from_json(self):
        """Test building from JSON string."""
        builder = RoadBuilder()
        json_str = json.dumps({
            "network_id": "json_network",
            "edges": [
                {"id": "seg_001", "road_type": "arterial"}
            ]
        })

        network = builder.build_from_json(json_str)

        assert network.network_id == "json_network"
        assert len(network.segments) == 1

    def test_build_segment_uses_template(self):
        """Test that segment building uses templates."""
        builder = RoadBuilder()
        data = {"id": "seg_001", "road_type": "highway"}

        segment = builder._build_segment(data)

        # Highway template has 3 lanes
        assert len(segment.lanes) == 3
        assert segment.speed_limit == 120

    def test_build_segment_custom_lanes(self):
        """Test segment building with custom lanes."""
        builder = RoadBuilder()
        data = {
            "id": "seg_001",
            "road_type": "local",
            "lanes": [
                {"type": "travel", "width": 4.0},
                {"type": "bike", "width": 1.5},
            ]
        }

        segment = builder._build_segment(data)

        assert len(segment.lanes) == 2
        assert segment.lanes[0].width == 4.0
        assert segment.lanes[1].lane_type == "bike"

    def test_to_gn_input(self):
        """Test converting to GN input format."""
        builder = RoadBuilder()
        network = RoadNetwork(
            network_id="test",
            segments=[RoadSegment(segment_id="seg_001")],
        )

        gn_data = builder.to_gn_input(network)

        assert "version" in gn_data
        assert "network" in gn_data
        assert "global_settings" in gn_data
        assert "materials" in gn_data

    def test_calculate_curve_length_straight(self):
        """Test curve length calculation for straight line."""
        builder = RoadBuilder()
        segment = RoadSegment(
            control_points=[(0.0, 0.0), (100.0, 0.0)]
        )

        length = builder.calculate_curve_length(segment)
        assert length == pytest.approx(100.0, rel=0.01)

    def test_calculate_curve_length_diagonal(self):
        """Test curve length calculation for diagonal."""
        builder = RoadBuilder()
        segment = RoadSegment(
            control_points=[(0.0, 0.0), (3.0, 4.0)]
        )

        length = builder.calculate_curve_length(segment)
        assert length == pytest.approx(5.0, rel=0.01)

    def test_calculate_curve_length_empty(self):
        """Test curve length with no points."""
        builder = RoadBuilder()
        segment = RoadSegment()

        length = builder.calculate_curve_length(segment)
        assert length == 0.0

    def test_calculate_curve_length_multiple_points(self):
        """Test curve length with multiple points."""
        builder = RoadBuilder()
        segment = RoadSegment(
            control_points=[(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)]
        )

        length = builder.calculate_curve_length(segment)
        assert length == pytest.approx(20.0, rel=0.01)


class TestRoadBuilderGN:
    """Tests for RoadBuilderGN class."""

    def test_create_node_group_spec(self):
        """Test creating node group specification."""
        spec = RoadBuilderGN.create_node_group_spec()

        assert spec["name"] == "Road_Builder"
        assert "inputs" in spec
        assert "outputs" in spec
        assert "Network_Data" in spec["inputs"]
        assert "Geometry" in spec["outputs"]

    def test_node_group_spec_has_required_inputs(self):
        """Test that node group spec has required inputs."""
        spec = RoadBuilderGN.create_node_group_spec()
        required_inputs = ["Network_Data", "Default_Lane_Width", "Curb_Height"]

        for input_name in required_inputs:
            assert input_name in spec["inputs"]

    def test_node_group_spec_has_required_outputs(self):
        """Test that node group spec has required outputs."""
        spec = RoadBuilderGN.create_node_group_spec()
        required_outputs = ["Geometry", "Road_Surface", "Markings", "Curbs"]

        for output_name in required_outputs:
            assert output_name in spec["outputs"]


class TestBuildRoadNetwork:
    """Tests for build_road_network convenience function."""

    def test_build_road_network_basic(self):
        """Test basic road network building."""
        data = {
            "network_id": "test",
            "edges": [{"id": "seg_001"}],
        }

        network = build_road_network(data)

        assert network.network_id == "test"
        assert len(network.segments) == 1

    def test_build_road_network_with_options(self):
        """Test road network building with options."""
        data = {"edges": [{"id": "seg_001", "road_type": "highway"}]}

        network = build_road_network(data, default_lane_width=4.0)

        # Highway template lanes should be applied
        assert len(network.segments[0].lanes) > 0


class TestNetworkToGNFormat:
    """Tests for network_to_gn_format convenience function."""

    def test_network_to_gn_format_basic(self):
        """Test basic network to GN format conversion."""
        network = RoadNetwork(network_id="test")

        gn_data = network_to_gn_format(network)

        assert gn_data["network"]["network_id"] == "test"

    def test_network_to_gn_format_with_segments(self):
        """Test GN format conversion with segments."""
        network = RoadNetwork(
            segments=[RoadSegment(segment_id="seg_001")],
            intersections=[IntersectionGeometry(intersection_id="int_001")],
        )

        gn_data = network_to_gn_format(network)

        assert len(gn_data["network"]["segments"]) == 1
        assert len(gn_data["network"]["intersections"]) == 1


class TestRoadBuilderEdgeCases:
    """Edge case tests for RoadBuilder."""

    def test_build_from_dict_no_edges(self):
        """Test building with no edges."""
        builder = RoadBuilder()
        data = {"network_id": "empty"}

        network = builder.build_from_dict(data)

        assert len(network.segments) == 0

    def test_build_segment_unknown_type(self):
        """Test building segment with unknown road type."""
        builder = RoadBuilder()
        data = {"id": "seg_001", "road_type": "unknown_type"}

        segment = builder._build_segment(data)

        # Should fall back to local template
        assert segment.road_type == "unknown_type"
        assert len(segment.lanes) > 0  # Uses local template lanes

    def test_build_intersection_roundabout(self):
        """Test building roundabout intersection."""
        builder = RoadBuilder()
        data = {
            "id": "int_001",
            "type": "roundabout",
            "position": [50.0, 50.0],
            "radius": 20.0,
        }

        intersection = builder._build_intersection(data)

        assert intersection.intersection_type == "roundabout"
        assert intersection.radius == 20.0

    def test_build_intersection_3way(self):
        """Test building 3-way intersection."""
        builder = RoadBuilder()
        data = {
            "id": "int_001",
            "type": "intersection_3way",
            "position": [50.0, 50.0],
        }

        intersection = builder._build_intersection(data)

        assert intersection.intersection_type == "3way_t"

    def test_bounds_calculation(self):
        """Test bounds calculation from segments."""
        builder = RoadBuilder()
        data = {
            "edges": [
                {"id": "seg_001", "curve": [[0.0, 0.0], [100.0, 0.0]]},
                {"id": "seg_002", "curve": [[50.0, 50.0], [150.0, 100.0]]},
            ]
        }

        network = builder.build_from_dict(data)

        assert network.bounds[0] == pytest.approx(0.0, rel=0.01)  # min_x
        assert network.bounds[1] == pytest.approx(0.0, rel=0.01)  # min_y
        assert network.bounds[2] == pytest.approx(150.0, rel=0.01)  # max_x
        assert network.bounds[3] == pytest.approx(100.0, rel=0.01)  # max_y

    def test_curve_with_control_points(self):
        """Test building segment with curve control points."""
        builder = RoadBuilder()
        data = {
            "id": "seg_001",
            "curve": [[0.0, 0.0], [25.0, 10.0], [50.0, 0.0], [100.0, 0.0]],
        }

        segment = builder._build_segment(data)

        assert len(segment.control_points) == 4
