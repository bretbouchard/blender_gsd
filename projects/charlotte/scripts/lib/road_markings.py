"""
Charlotte Digital Twin - Road Markings System

Comprehensive road marking specifications and generation for:
- Center lines (yellow, double solid)
- Lane dividers (white, dashed)
- Edge lines (white, solid)
- Crosswalks (zebra stripes)
- Stop lines (white, solid)
- Turn arrows
- Traffic signals
- Manholes

Uses OSM lanes data where available, estimates from road class otherwise.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import math


# =============================================================================
# ROAD WIDTH ESTIMATION
# =============================================================================

# Standard lane widths
STANDARD_LANE_WIDTH = 3.5  # meters (US standard)

# Road class to typical lanes mapping (from Charlotte OSM data analysis)
ROAD_CLASS_LANES = {
    'motorway': 3.4,       # Average from data
    'motorway_link': 1.8,
    'primary': 3.3,
    'primary_link': 1.1,
    'secondary': 3.0,
    'secondary_link': 1.2,
    'tertiary': 2.2,
    'residential': 2.0,
    'living_street': 2.0,
    'service': 2.0,
    'unclassified': 2.0,
    'footway': 0.5,  # Not really lanes, just for width calc
    'cycleway': 0.5,
    'pedestrian': 0.5,
    'path': 0.5,
    'steps': 0.5,
}

# Road class to additional width (shoulders, parking, etc.)
ROAD_CLASS_EXTRA_WIDTH = {
    'motorway': 6.0,      # Shoulders both sides
    'motorway_link': 3.0,
    'primary': 2.0,       # Some shoulder
    'primary_link': 1.0,
    'secondary': 1.5,
    'secondary_link': 1.0,
    'tertiary': 1.0,
    'residential': 3.0,   # Parking both sides
    'living_street': 2.0,
    'service': 0.5,
    'unclassified': 0.5,
    'footway': 0.0,
    'cycleway': 0.0,
    'pedestrian': 0.0,
    'path': 0.0,
    'steps': 0.0,
}


def estimate_road_width(
    highway_type: str,
    explicit_width: Optional[float] = None,
    explicit_lanes: Optional[int] = None
) -> Tuple[float, int]:
    """
    Estimate road width based on available data.

    Priority:
    1. Explicit width from OSM
    2. Explicit lanes * lane width
    3. Typical lanes for road class * lane width

    Returns:
        (width_meters, estimated_lanes)
    """
    # Use explicit width if available
    if explicit_width and explicit_width > 0:
        lanes = explicit_lanes or int(round(explicit_width / STANDARD_LANE_WIDTH))
        return (explicit_width, max(1, lanes))

    # Calculate from lanes
    if explicit_lanes and explicit_lanes > 0:
        width = explicit_lanes * STANDARD_LANE_WIDTH
        width += ROAD_CLASS_EXTRA_WIDTH.get(highway_type, 1.0)
        return (width, explicit_lanes)

    # Estimate from road class
    typical_lanes = ROAD_CLASS_LANES.get(highway_type, 2.0)
    width = typical_lanes * STANDARD_LANE_WIDTH
    width += ROAD_CLASS_EXTRA_WIDTH.get(highway_type, 1.0)

    return (width, max(1, int(round(typical_lanes))))


# =============================================================================
# MARKING SPECIFICATIONS
# =============================================================================

class MarkingType(Enum):
    """Types of road markings."""
    CENTER_LINE = "center_line"           # Yellow, double solid
    CENTER_LINE_DASHED = "center_dashed"  # Yellow, dashed (passing zone)
    LANE_DIVIDER = "lane_divider"         # White, dashed
    EDGE_LINE = "edge_line"               # White, solid
    CROSSWALK = "crosswalk"               # White zebra stripes
    STOP_LINE = "stop_line"               # White, solid across road
    TURN_ARROW_LEFT = "turn_left"
    TURN_ARROW_RIGHT = "turn_right"
    TURN_ARROW_STRAIGHT = "turn_straight"
    YIELD_LINE = "yield_line"             # White triangles
    SPEED_HUMP = "speed_hump"             # White triangles


@dataclass
class MarkingSpec:
    """Specification for a road marking."""
    marking_type: MarkingType
    color: Tuple[float, float, float, float]  # RGBA (white or yellow)
    width: float          # Marking width in meters
    length: float         # Marking length in meters
    spacing: float        # Gap between markings (for dashed)
    offset_from_center: float  # Offset from road center
    is_dashed: bool = False
    dash_length: float = 3.0
    dash_gap: float = 9.0

    @property
    def is_yellow(self) -> bool:
        """Check if this is a yellow marking."""
        return self.color[1] < 0.9  # Yellow has less green


# Standard marking colors
COLOR_WHITE = (1.0, 1.0, 1.0, 1.0)
COLOR_YELLOW = (1.0, 0.85, 0.0, 1.0)


# Standard marking specifications
MARKING_SPECS: Dict[MarkingType, MarkingSpec] = {

    # Center line (double yellow solid)
    MarkingType.CENTER_LINE: MarkingSpec(
        marking_type=MarkingType.CENTER_LINE,
        color=COLOR_YELLOW,
        width=0.15,      # 15cm per line
        length=0.3,      # Double line spacing
        spacing=0.0,     # Solid
        offset_from_center=0.0,
        is_dashed=False,
    ),

    # Center line dashed (passing zone)
    MarkingType.CENTER_LINE_DASHED: MarkingSpec(
        marking_type=MarkingType.CENTER_LINE_DASHED,
        color=COLOR_YELLOW,
        width=0.15,
        length=3.0,
        spacing=9.0,
        offset_from_center=0.0,
        is_dashed=True,
        dash_length=3.0,
        dash_gap=9.0,
    ),

    # Lane divider (white dashed)
    MarkingType.LANE_DIVIDER: MarkingSpec(
        marking_type=MarkingType.LANE_DIVIDER,
        color=COLOR_WHITE,
        width=0.15,      # 15cm
        length=3.0,
        spacing=9.0,
        offset_from_center=0.0,  # Calculated per lane
        is_dashed=True,
        dash_length=3.0,
        dash_gap=9.0,
    ),

    # Edge line (white solid)
    MarkingType.EDGE_LINE: MarkingSpec(
        marking_type=MarkingType.EDGE_LINE,
        color=COLOR_WHITE,
        width=0.20,      # 20cm
        length=0.0,      # Continuous
        spacing=0.0,
        offset_from_center=0.0,  # At road edge
        is_dashed=False,
    ),

    # Crosswalk
    MarkingType.CROSSWALK: MarkingSpec(
        marking_type=MarkingType.CROSSWALK,
        color=COLOR_WHITE,
        width=0.40,      # 40cm stripes
        length=3.0,      # 3m deep
        spacing=0.60,    # 60cm gaps
        offset_from_center=0.0,
        is_dashed=False,
    ),

    # Stop line
    MarkingType.STOP_LINE: MarkingSpec(
        marking_type=MarkingType.STOP_LINE,
        color=COLOR_WHITE,
        width=0.60,      # 60cm thick
        length=0.0,      # Full road width
        spacing=0.0,
        offset_from_center=0.0,
        is_dashed=False,
    ),
}


# =============================================================================
# ROAD MARKING RULES BY CLASS
# =============================================================================

@dataclass
class RoadMarkingRules:
    """Rules for which markings apply to a road class."""
    has_center_line: bool = True
    center_line_type: MarkingType = MarkingType.CENTER_LINE
    has_edge_lines: bool = True
    has_lane_dividers: bool = False
    min_lanes_for_dividers: int = 3
    has_crosswalks: bool = True
    has_stop_lines: bool = True


# Marking rules by road class
ROAD_MARKING_RULES: Dict[str, RoadMarkingRules] = {
    'motorway': RoadMarkingRules(
        has_center_line=True,
        center_line_type=MarkingType.CENTER_LINE,
        has_edge_lines=True,
        has_lane_dividers=True,
        min_lanes_for_dividers=4,
        has_crosswalks=False,  # No pedestrians on highways
        has_stop_lines=False,
    ),
    'motorway_link': RoadMarkingRules(
        has_center_line=False,  # Usually one-way
        has_edge_lines=True,
        has_lane_dividers=False,
        has_crosswalks=False,
        has_stop_lines=True,    # At merge points
    ),
    'primary': RoadMarkingRules(
        has_center_line=True,
        center_line_type=MarkingType.CENTER_LINE,
        has_edge_lines=True,
        has_lane_dividers=True,
        min_lanes_for_dividers=3,
        has_crosswalks=True,
        has_stop_lines=True,
    ),
    'secondary': RoadMarkingRules(
        has_center_line=True,
        center_line_type=MarkingType.CENTER_LINE,
        has_edge_lines=True,
        has_lane_dividers=True,
        min_lanes_for_dividers=3,
        has_crosswalks=True,
        has_stop_lines=True,
    ),
    'tertiary': RoadMarkingRules(
        has_center_line=True,
        center_line_type=MarkingType.CENTER_LINE,
        has_edge_lines=True,
        has_lane_dividers=False,
        has_crosswalks=True,
        has_stop_lines=True,
    ),
    'residential': RoadMarkingRules(
        has_center_line=True,
        center_line_type=MarkingType.CENTER_LINE_DASHED,  # Often passing allowed
        has_edge_lines=False,   # Often no edge lines
        has_lane_dividers=False,
        has_crosswalks=False,   # Usually no marked crosswalks
        has_stop_lines=True,
    ),
    'living_street': RoadMarkingRules(
        has_center_line=False,
        has_edge_lines=False,
        has_lane_dividers=False,
        has_crosswalks=False,
        has_stop_lines=False,
    ),
    'service': RoadMarkingRules(
        has_center_line=False,
        has_edge_lines=False,
        has_lane_dividers=False,
        has_crosswalks=False,
        has_stop_lines=False,
    ),
}

# Default rules
DEFAULT_MARKING_RULES = RoadMarkingRules()


def get_marking_rules(highway_type: str) -> RoadMarkingRules:
    """Get marking rules for a road type."""
    return ROAD_MARKING_RULES.get(highway_type, DEFAULT_MARKING_RULES)


# =============================================================================
# STREET LIGHT PLACEMENT
# =============================================================================

@dataclass
class StreetLightSpec:
    """Specification for street light placement."""
    spacing: float         # Meters between lights
    offset_from_edge: float  # Meters from road edge
    height: float          # Pole height
    has_double_side: bool  # Lights on both sides

    def get_positions_along_road(
        self,
        road_length: float,
        road_width: float
    ) -> List[Tuple[float, float]]:
        """
        Calculate light positions along a road segment.

        Returns:
            List of (distance_along_road, lateral_offset) tuples
        """
        positions = []
        num_lights = int(road_length / self.spacing) + 1

        for i in range(num_lights):
            dist = i * self.spacing
            if dist > road_length:
                break

            # Right side
            positions.append((dist, self.offset_from_edge))

            # Left side if double
            if self.has_double_side:
                positions.append((dist, road_width + self.offset_from_edge))

        return positions


# Street light specs by road class
STREET_LIGHT_SPECS: Dict[str, StreetLightSpec] = {
    'motorway': StreetLightSpec(
        spacing=50.0,
        offset_from_edge=2.0,
        height=12.0,
        has_double_side=True,
    ),
    'motorway_link': StreetLightSpec(
        spacing=50.0,
        offset_from_edge=2.0,
        height=12.0,
        has_double_side=False,
    ),
    'primary': StreetLightSpec(
        spacing=30.0,
        offset_from_edge=1.5,
        height=10.0,
        has_double_side=True,
    ),
    'secondary': StreetLightSpec(
        spacing=40.0,
        offset_from_edge=1.5,
        height=10.0,
        has_double_side=True,
    ),
    'tertiary': StreetLightSpec(
        spacing=50.0,
        offset_from_edge=1.0,
        height=8.0,
        has_double_side=False,
    ),
    'residential': StreetLightSpec(
        spacing=0.0,  # No lights typically
        offset_from_edge=0.5,
        height=6.0,
        has_double_side=False,
    ),
}

DEFAULT_STREET_LIGHT = StreetLightSpec(
    spacing=0.0,
    offset_from_edge=1.0,
    height=8.0,
    has_double_side=False,
)


def get_street_light_spec(highway_type: str) -> StreetLightSpec:
    """Get street light spec for a road type."""
    return STREET_LIGHT_SPECS.get(highway_type, DEFAULT_STREET_LIGHT)


# =============================================================================
# MANHOLE DISTRIBUTION
# =============================================================================

@dataclass
class ManholeSpec:
    """Specification for manhole placement."""
    spacing: float         # Meters between manholes
    offset_from_center: float  # Offset from lane center
    types: List[str]       # Types of manholes

    def get_positions_along_road(
        self,
        road_length: float,
        road_width: float,
        lanes: int
    ) -> List[Tuple[float, float, str]]:
        """
        Calculate manhole positions.

        Returns:
            List of (distance_along_road, lateral_offset, type) tuples
        """
        positions = []
        num_manholes = int(road_length / self.spacing) + 1

        for i in range(num_manholes):
            dist = i * self.spacing + (self.spacing / 2)  # Offset from start
            if dist > road_length:
                break

            # Alternate between manhole types
            mh_type = self.types[i % len(self.types)]

            # Place in lane (offset from center)
            if lanes >= 2:
                offset = road_width / 4  # In first lane
            else:
                offset = 0.0

            positions.append((dist, offset, mh_type))

        return positions


MANHOLE_SPEC = ManholeSpec(
    spacing=30.0,  # Every 30m
    offset_from_center=1.0,
    types=['sewer', 'water', 'gas', 'electric', 'telecom'],
)


# =============================================================================
# TRAFFIC SIGNAL PLACEMENT
# =============================================================================

@dataclass
class TrafficSignalSpec:
    """Specification for traffic signal placement."""
    has_signals: bool
    signal_height: float
    mast_arm_length: float
    has_pedestrian_signals: bool


TRAFFIC_SIGNAL_RULES: Dict[str, TrafficSignalSpec] = {
    'primary': TrafficSignalSpec(
        has_signals=True,
        signal_height=5.0,
        mast_arm_length=10.0,
        has_pedestrian_signals=True,
    ),
    'secondary': TrafficSignalSpec(
        has_signals=True,
        signal_height=5.0,
        mast_arm_length=8.0,
        has_pedestrian_signals=True,
    ),
    'tertiary': TrafficSignalSpec(
        has_signals=True,
        signal_height=4.5,
        mast_arm_length=6.0,
        has_pedestrian_signals=False,
    ),
    'residential': TrafficSignalSpec(
        has_signals=False,  # Usually stop signs
        signal_height=4.0,
        mast_arm_length=4.0,
        has_pedestrian_signals=False,
    ),
}

DEFAULT_TRAFFIC_SIGNAL = TrafficSignalSpec(
    has_signals=False,
    signal_height=4.5,
    mast_arm_length=5.0,
    has_pedestrian_signals=False,
)


def get_traffic_signal_spec(highway_type: str) -> TrafficSignalSpec:
    """Get traffic signal spec for a road type."""
    return TRAFFIC_SIGNAL_RULES.get(highway_type, DEFAULT_TRAFFIC_SIGNAL)


# =============================================================================
# EXPORT ALL SPECS
# =============================================================================

__all__ = [
    # Width estimation
    'estimate_road_width',
    'STANDARD_LANE_WIDTH',
    'ROAD_CLASS_LANES',
    'ROAD_CLASS_EXTRA_WIDTH',

    # Marking types and specs
    'MarkingType',
    'MarkingSpec',
    'MARKING_SPECS',
    'COLOR_WHITE',
    'COLOR_YELLOW',

    # Rules
    'RoadMarkingRules',
    'ROAD_MARKING_RULES',
    'get_marking_rules',

    # Street lights
    'StreetLightSpec',
    'STREET_LIGHT_SPECS',
    'get_street_light_spec',

    # Manholes
    'ManholeSpec',
    'MANHOLE_SPEC',

    # Traffic signals
    'TrafficSignalSpec',
    'TRAFFIC_SIGNAL_RULES',
    'get_traffic_signal_spec',
]
