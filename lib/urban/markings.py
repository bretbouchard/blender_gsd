"""
Road Markings System

Pavement markings including lane lines, crosswalks, arrows, and symbols.
MUTCD-compliant marking specifications and placement.

Implements REQ-UR-08: Crosswalk & Marking System.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum
import math


class MarkingColor(Enum):
    """Marking colors per MUTCD."""
    WHITE = "white"
    YELLOW = "yellow"
    BLUE = "blue"
    RED = "red"
    GREEN = "green"
    BLACK = "black"  # For contrast


class MarkingType(Enum):
    """Types of pavement markings."""
    # Lane lines
    SOLID_LINE = "solid_line"
    BROKEN_LINE = "broken_line"
    DOUBLE_SOLID = "double_solid"
    DOUBLE_BROKEN = "double_broken"
    SOLID_BROKEN = "solid_broken"
    BROKEN_SOLID = "broken_solid"

    # Crosswalks
    STANDARD_CROSSWALK = "standard_crosswalk"
    CONTINENTAL_CROSSWALK = "continental_crosswalk"
    LADDER_CROSSWALK = "ladder_crosswalk"
    ZEBRA_CROSSWALK = "zebra_crosswalk"

    # Arrows
    STRAIGHT_ARROW = "straight_arrow"
    LEFT_ARROW = "left_arrow"
    RIGHT_ARROW = "right_arrow"
    STRAIGHT_LEFT_ARROW = "straight_left_arrow"
    STRAIGHT_RIGHT_ARROW = "straight_right_arrow"
    LEFT_RIGHT_ARROW = "left_right_arrow"
    U_TURN_ARROW = "u_turn_arrow"
    MERGE_ARROW = "merge_arrow"

    # Symbols
    BIKE_SYMBOL = "bike_symbol"
    ONLY_WORD = "only_word"
    STOP_WORD = "stop_word"
    YIELD_WORD = "yield_word"
    SLOW_WORD = "slow_word"
    AHEAD_WORD = "ahead_word"
    RAILROAD_CROSSING = "railroad_crossing"
    HANDICAP_SYMBOL = "handicap_symbol"
    SPEED_HUMP = "speed_hump"

    # Special
    STOP_BAR = "stop_bar"
    YIELD_LINE = "yield_line"
    CROSSWALK_AHEAD = "crosswalk_ahead"
    SPEED_LIMIT = "speed_limit"


class MarkingMaterial(Enum):
    """Marking material types."""
    PAINT = "paint"
    THERMOPLASTIC = "thermoplastic"
    EPOXY = "epoxy"
    TAPE = "tape"
    POLYUREA = "polyurea"
    METHYL_METHACRYLATE = "mma"


@dataclass
class MarkingSpec:
    """
    Pavement marking specification.

    Attributes:
        marking_id: Unique marking identifier
        marking_type: Type of marking
        color: Marking color
        width: Width of line/element in meters
        length: Length in meters (for lines)
        spacing: Spacing for broken lines in meters
        stroke_ratio: Ratio of painted to gap (broken lines)
        material: Material type
        reflectivity: Reflectivity level (0-100%)
        thickness: Material thickness in mm
        is_retroreflective: Has glass beads for reflectivity
    """
    marking_id: str = ""
    marking_type: str = "solid_line"
    color: str = "white"
    width: float = 0.15
    length: float = 3.0
    spacing: float = 3.0
    stroke_ratio: float = 1.0
    material: str = "thermoplastic"
    reflectivity: float = 80.0
    thickness: float = 3.0
    is_retroreflective: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "marking_id": self.marking_id,
            "marking_type": self.marking_type,
            "color": self.color,
            "width": self.width,
            "length": self.length,
            "spacing": self.spacing,
            "stroke_ratio": self.stroke_ratio,
            "material": self.material,
            "reflectivity": self.reflectivity,
            "thickness": self.thickness,
            "is_retroreflective": self.is_retroreflective,
        }


@dataclass
class MarkingInstance:
    """
    Placed marking instance.

    Attributes:
        instance_id: Unique instance identifier
        spec: Marking specification
        start: Start point (x, y)
        end: End point (x, y)
        rotation: Rotation angle in degrees (for symbols)
        lane_id: Associated lane ID
    """
    instance_id: str = ""
    spec: Optional[MarkingSpec] = None
    start: Tuple[float, float] = (0.0, 0.0)
    end: Tuple[float, float] = (1.0, 0.0)
    rotation: float = 0.0
    lane_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "instance_id": self.instance_id,
            "spec": self.spec.to_dict() if self.spec else None,
            "start": list(self.start),
            "end": list(self.end),
            "rotation": self.rotation,
            "lane_id": self.lane_id,
        }


# =============================================================================
# STANDARD MARKING SPECIFICATIONS
# =============================================================================

LANE_LINE_MARKINGS: Dict[str, MarkingSpec] = {
    # White lane lines (same direction)
    "WL-4-BROKEN": MarkingSpec(
        marking_id="WL-4-BROKEN",
        marking_type="broken_line",
        color="white",
        width=0.10,
        length=3.0,
        spacing=9.0,
        stroke_ratio=0.33,
        material="thermoplastic",
    ),
    "WL-6-SOLID": MarkingSpec(
        marking_id="WL-6-SOLID",
        marking_type="solid_line",
        color="white",
        width=0.15,
        length=0.0,  # Continuous
        material="thermoplastic",
    ),
    "WL-8-SOLID": MarkingSpec(
        marking_id="WL-8-SOLID",
        marking_type="solid_line",
        color="white",
        width=0.20,
        length=0.0,
        material="thermoplastic",
    ),
    "WL-EDGE-SOLID": MarkingSpec(
        marking_id="WL-EDGE-SOLID",
        marking_type="solid_line",
        color="white",
        width=0.15,
        length=0.0,
        material="thermoplastic",
    ),

    # Yellow center lines (opposite direction)
    "YL-4-BROKEN": MarkingSpec(
        marking_id="YL-4-BROKEN",
        marking_type="broken_line",
        color="yellow",
        width=0.10,
        length=3.0,
        spacing=9.0,
        stroke_ratio=0.33,
        material="thermoplastic",
    ),
    "YL-DOUBLE-SOLID": MarkingSpec(
        marking_id="YL-DOUBLE-SOLID",
        marking_type="double_solid",
        color="yellow",
        width=0.10,
        length=0.0,
        spacing=0.10,  # Gap between lines
        material="thermoplastic",
    ),
    "YL-SOLID-BROKEN": MarkingSpec(
        marking_id="YL-SOLID-BROKEN",
        marking_type="solid_broken",
        color="yellow",
        width=0.10,
        length=3.0,
        spacing=9.0,
        stroke_ratio=0.33,
        material="thermoplastic",
    ),

    # No-passing zone
    "YL-NO-PASS": MarkingSpec(
        marking_id="YL-NO-PASS",
        marking_type="double_solid",
        color="yellow",
        width=0.10,
        length=0.0,
        spacing=0.10,
        material="thermoplastic",
    ),
}

CROSSWALK_MARKINGS: Dict[str, MarkingSpec] = {
    "CW-STANDARD": MarkingSpec(
        marking_id="CW-STANDARD",
        marking_type="standard_crosswalk",
        color="white",
        width=0.30,
        length=3.0,  # Crosswalk width
        spacing=0.30,
        material="thermoplastic",
    ),
    "CW-CONTINENTAL": MarkingSpec(
        marking_id="CW-CONTINENTAL",
        marking_type="continental_crosswalk",
        color="white",
        width=0.40,
        length=3.0,
        spacing=0.60,
        material="thermoplastic",
    ),
    "CW-LADDER": MarkingSpec(
        marking_id="CW-LADDER",
        marking_type="ladder_crosswalk",
        color="white",
        width=0.30,
        length=3.0,
        spacing=0.45,
        material="thermoplastic",
    ),
    "CW-ZEBRA": MarkingSpec(
        marking_id="CW-ZEBRA",
        marking_type="zebra_crosswalk",
        color="white",
        width=0.40,
        length=3.0,
        spacing=0.60,
        material="thermoplastic",
    ),
    "CW-HIGH-VIS": MarkingSpec(
        marking_id="CW-HIGH-VIS",
        marking_type="continental_crosswalk",
        color="white",
        width=0.50,
        length=4.0,
        spacing=0.50,
        material="thermoplastic",
        reflectivity=95.0,
    ),
}

SYMBOL_MARKINGS: Dict[str, MarkingSpec] = {
    # Arrows
    "ARROW-STRAIGHT": MarkingSpec(
        marking_id="ARROW-STRAIGHT",
        marking_type="straight_arrow",
        color="white",
        width=0.60,
        length=3.0,
        material="thermoplastic",
    ),
    "ARROW-LEFT": MarkingSpec(
        marking_id="ARROW-LEFT",
        marking_type="left_arrow",
        color="white",
        width=0.60,
        length=3.0,
        material="thermoplastic",
    ),
    "ARROW-RIGHT": MarkingSpec(
        marking_id="ARROW-RIGHT",
        marking_type="right_arrow",
        color="white",
        width=0.60,
        length=3.0,
        material="thermoplastic",
    ),
    "ARROW-STRAIGHT-LEFT": MarkingSpec(
        marking_id="ARROW-STRAIGHT-LEFT",
        marking_type="straight_left_arrow",
        color="white",
        width=1.0,
        length=3.5,
        material="thermoplastic",
    ),
    "ARROW-UTURN": MarkingSpec(
        marking_id="ARROW-UTURN",
        marking_type="u_turn_arrow",
        color="white",
        width=0.80,
        length=2.5,
        material="thermoplastic",
    ),

    # Words
    "WORD-STOP": MarkingSpec(
        marking_id="WORD-STOP",
        marking_type="stop_word",
        color="white",
        width=2.0,
        length=6.0,  # Total length of word
        material="thermoplastic",
    ),
    "WORD-YIELD": MarkingSpec(
        marking_id="WORD-YIELD",
        marking_type="yield_word",
        color="white",
        width=1.8,
        length=6.5,
        material="thermoplastic",
    ),
    "WORD-ONLY": MarkingSpec(
        marking_id="WORD-ONLY",
        marking_type="only_word",
        color="white",
        width=1.2,
        length=4.5,
        material="thermoplastic",
    ),
    "WORD-SLOW": MarkingSpec(
        marking_id="WORD-SLOW",
        marking_type="slow_word",
        color="white",
        width=1.5,
        length=5.0,
        material="thermoplastic",
    ),

    # Symbols
    "SYMBOL-BIKE": MarkingSpec(
        marking_id="SYMBOL-BIKE",
        marking_type="bike_symbol",
        color="white",
        width=0.60,
        length=1.5,
        material="thermoplastic",
    ),
    "SYMBOL-HANDICAP": MarkingSpec(
        marking_id="SYMBOL-HANDICAP",
        marking_type="handicap_symbol",
        color="blue",
        width=1.0,
        length=1.5,
        material="thermoplastic",
    ),
    "SYMBOL-RAILROAD": MarkingSpec(
        marking_id="SYMBOL-RAILROAD",
        marking_type="railroad_crossing",
        color="white",
        width=2.0,
        length=2.0,
        material="thermoplastic",
    ),
}

SPECIAL_MARKINGS: Dict[str, MarkingSpec] = {
    "STOP-BAR": MarkingSpec(
        marking_id="STOP-BAR",
        marking_type="stop_bar",
        color="white",
        width=0.60,
        length=3.5,  # Width of lane
        material="thermoplastic",
    ),
    "YIELD-LINE": MarkingSpec(
        marking_id="YIELD-LINE",
        marking_type="yield_line",
        color="white",
        width=0.30,
        length=3.0,
        spacing=0.30,
        material="thermoplastic",
    ),
    "SPEED-HUMP": MarkingSpec(
        marking_id="SPEED-HUMP",
        marking_type="speed_hump",
        color="yellow",
        width=0.10,
        length=3.5,
        spacing=0.20,
        material="thermoplastic",
    ),
}

# Combined catalog
MARKING_CATALOG: Dict[str, MarkingSpec] = {}
MARKING_CATALOG.update(LANE_LINE_MARKINGS)
MARKING_CATALOG.update(CROSSWALK_MARKINGS)
MARKING_CATALOG.update(SYMBOL_MARKINGS)
MARKING_CATALOG.update(SPECIAL_MARKINGS)


@dataclass
class CrosswalkGeometry:
    """
    Generated crosswalk geometry.

    Attributes:
        crosswalk_id: Unique crosswalk ID
        position: Center position (x, y, z)
        width: Crosswalk width (perpendicular to road)
        length: Crosswalk length (across road)
        direction: Direction of crossing in degrees
        marking_type: Type of crosswalk marking
        stripes: List of stripe rectangles (start, end pairs)
    """
    crosswalk_id: str = ""
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    width: float = 3.0
    length: float = 6.0
    direction: float = 0.0
    marking_type: str = "CW-CONTINENTAL"
    stripes: List[Tuple[Tuple[float, float], Tuple[float, float]]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "crosswalk_id": self.crosswalk_id,
            "position": list(self.position),
            "width": self.width,
            "length": self.length,
            "direction": self.direction,
            "marking_type": self.marking_type,
            "stripes": [(list(s), list(e)) for s, e in self.stripes],
        }


class MarkingPlacer:
    """
    Places road markings along road network.

    Usage:
        placer = MarkingPlacer()
        markings = placer.place_lane_markings(road_segments, lane_config)
        crosswalks = placer.place_crosswalks_at_intersection(intersection)
    """

    def __init__(self):
        """Initialize marking placer."""
        self.catalog = MARKING_CATALOG

    def get_marking(self, marking_id: str) -> Optional[MarkingSpec]:
        """Get marking specification by ID."""
        return self.catalog.get(marking_id)

    def place_lane_markings(
        self,
        road_segments: List[Tuple[Tuple[float, float], Tuple[float, float]]],
        lane_count: int = 2,
        lane_width: float = 3.5,
        is_divided: bool = False,
        center_marking: str = "YL-DOUBLE-SOLID",
        lane_marking: str = "WL-4-BROKEN",
        edge_marking: str = "WL-EDGE-SOLID",
    ) -> List[MarkingInstance]:
        """
        Place lane markings along road.

        Args:
            road_segments: List of (start, end) point tuples
            lane_count: Number of lanes per direction
            lane_width: Width of each lane
            is_divided: Whether road has median
            center_marking: Center line marking ID
            lane_marking: Lane line marking ID
            edge_marking: Edge line marking ID

        Returns:
            List of MarkingInstance
        """
        markings = []

        center_spec = self.catalog.get(center_marking)
        lane_spec = self.catalog.get(lane_marking)
        edge_spec = self.catalog.get(edge_marking)

        if not center_spec or not lane_spec:
            return markings

        for seg_idx, (start, end) in enumerate(road_segments):
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            length = math.sqrt(dx * dx + dy * dy)
            angle = math.degrees(math.atan2(dy, dx))

            # Unit vectors
            along_x = dx / length if length > 0 else 0
            along_y = dy / length if length > 0 else 0
            perp_x = -along_y
            perp_y = along_x

            # Center line
            markings.append(MarkingInstance(
                instance_id=f"center_{seg_idx}",
                spec=center_spec,
                start=start,
                end=end,
                lane_id="center",
            ))

            # Edge lines
            half_road = (lane_count * lane_width) / 2

            # Right edge
            edge_start = (start[0] + half_road * perp_x, start[1] + half_road * perp_y)
            edge_end = (end[0] + half_road * perp_x, end[1] + half_road * perp_y)
            if edge_spec:
                markings.append(MarkingInstance(
                    instance_id=f"edge_r_{seg_idx}",
                    spec=edge_spec,
                    start=edge_start,
                    end=edge_end,
                    lane_id="edge_right",
                ))

            # Left edge
            edge_start = (start[0] - half_road * perp_x, start[1] - half_road * perp_y)
            edge_end = (end[0] - half_road * perp_x, end[1] - half_road * perp_y)
            if edge_spec:
                markings.append(MarkingInstance(
                    instance_id=f"edge_l_{seg_idx}",
                    spec=edge_spec,
                    start=edge_start,
                    end=edge_end,
                    lane_id="edge_left",
                ))

            # Lane lines
            for lane in range(1, lane_count):
                offset = lane * lane_width - (lane_count * lane_width / 2) + lane_width / 2

                lane_start = (start[0] + offset * perp_x, start[1] + offset * perp_y)
                lane_end = (end[0] + offset * perp_x, end[1] + offset * perp_y)

                markings.append(MarkingInstance(
                    instance_id=f"lane_{seg_idx}_{lane}",
                    spec=lane_spec,
                    start=lane_start,
                    end=lane_end,
                    lane_id=f"lane_{lane}",
                ))

        return markings

    def place_crosswalk(
        self,
        position: Tuple[float, float, float],
        direction: float,
        width: float = 3.0,
        length: float = 6.0,
        marking_type: str = "CW-CONTINENTAL",
    ) -> CrosswalkGeometry:
        """
        Generate crosswalk geometry.

        Args:
            position: Center position (x, y, z)
            direction: Direction of crossing in degrees
            width: Width of crosswalk (stripe length)
            length: Length across road
            marking_type: Type of crosswalk marking

        Returns:
            CrosswalkGeometry with stripe positions
        """
        spec = self.catalog.get(marking_type)
        if not spec:
            spec = CROSSWALK_MARKINGS.get("CW-CONTINENTAL")

        x, y, z = position
        rad = math.radians(direction)

        # Direction vectors
        along_x = math.cos(rad)
        along_y = math.sin(rad)
        perp_x = -along_y
        perp_y = along_x

        crosswalk = CrosswalkGeometry(
            crosswalk_id=f"cw_{x:.0f}_{y:.0f}",
            position=position,
            width=width,
            length=length,
            direction=direction,
            marking_type=marking_type,
        )

        # Generate stripes based on marking type
        if marking_type in ["CW-CONTINENTAL", "CW-LADDER", "CW-HIGH-VIS"]:
            stripe_width = spec.width
            spacing = spec.spacing

            num_stripes = int(length / spacing)
            start_offset = (length - (num_stripes - 1) * spacing) / 2

            for i in range(num_stripes):
                stripe_pos = start_offset + i * spacing

                stripe_start = (
                    x - (width / 2) * perp_x + stripe_pos * along_x,
                    y - (width / 2) * perp_y + stripe_pos * along_y,
                )
                stripe_end = (
                    x + (width / 2) * perp_x + stripe_pos * along_x,
                    y + (width / 2) * perp_y + stripe_pos * along_y,
                )
                crosswalk.stripes.append((stripe_start, stripe_end))

        elif marking_type == "CW-STANDARD":
            # Two parallel lines
            stripe_width = spec.width

            for offset_mult in [-1, 1]:
                offset = offset_mult * (length / 2 - stripe_width / 2)

                stripe_start = (
                    x - (width / 2) * perp_x + offset * along_x,
                    y - (width / 2) * perp_y + offset * along_y,
                )
                stripe_end = (
                    x + (width / 2) * perp_x + offset * along_x,
                    y + (width / 2) * perp_y + offset * along_y,
                )
                crosswalk.stripes.append((stripe_start, stripe_end))

        elif marking_type == "CW-ZEBRA":
            # Diagonal stripes
            stripe_width = spec.width
            spacing = spec.spacing

            # Diagonal stripes
            num_stripes = int((length + width) / spacing)

            for i in range(num_stripes):
                # Calculate stripe position
                stripe_offset = i * spacing - length / 2

                # Diagonal stripe endpoints
                p1_along = stripe_offset
                p1_perp = -width / 2
                p2_along = stripe_offset + width
                p2_perp = width / 2

                stripe_start = (
                    x + p1_along * along_x + p1_perp * perp_x,
                    y + p1_along * along_y + p1_perp * perp_y,
                )
                stripe_end = (
                    x + p2_along * along_x + p2_perp * perp_x,
                    y + p2_along * along_y + p2_perp * perp_y,
                )
                crosswalk.stripes.append((stripe_start, stripe_end))

        return crosswalk

    def place_crosswalks_at_intersection(
        self,
        position: Tuple[float, float, float],
        intersection_type: str = "4way",
        road_width: float = 10.0,
        marking_type: str = "CW-CONTINENTAL",
    ) -> List[CrosswalkGeometry]:
        """
        Place crosswalks at intersection.

        Args:
            position: Intersection center position
            intersection_type: Type of intersection
            road_width: Width of approaching roads
            marking_type: Type of crosswalk marking

        Returns:
            List of CrosswalkGeometry
        """
        crosswalks = []
        x, y, z = position

        if intersection_type in ["4way", "intersection_4way"]:
            for angle in [0, 90, 180, 270]:
                offset = road_width / 2 + 2.0
                rad = math.radians(angle)
                cw_x = x + offset * math.cos(rad)
                cw_y = y + offset * math.sin(rad)

                crosswalk = self.place_crosswalk(
                    position=(cw_x, cw_y, z),
                    direction=angle + 90,
                    width=road_width - 2,
                    length=3.0,
                    marking_type=marking_type,
                )
                crosswalks.append(crosswalk)

        elif intersection_type in ["3way", "intersection_3way"]:
            for angle in [0, 120, 240]:
                offset = road_width / 2 + 2.0
                rad = math.radians(angle)
                cw_x = x + offset * math.cos(rad)
                cw_y = y + offset * math.sin(rad)

                crosswalk = self.place_crosswalk(
                    position=(cw_x, cw_y, z),
                    direction=angle + 90,
                    width=road_width - 2,
                    length=3.0,
                    marking_type=marking_type,
                )
                crosswalks.append(crosswalk)

        elif intersection_type == "roundabout":
            for angle in [0, 90, 180, 270]:
                offset = 12.0
                rad = math.radians(angle)
                cw_x = x + offset * math.cos(rad)
                cw_y = y + offset * math.sin(rad)

                crosswalk = self.place_crosswalk(
                    position=(cw_x, cw_y, z),
                    direction=angle + 90,
                    width=8.0,
                    length=3.0,
                    marking_type=marking_type,
                )
                crosswalks.append(crosswalk)

        return crosswalks

    def place_stop_bars(
        self,
        intersection_position: Tuple[float, float, float],
        approach_angles: List[float],
        distance_from_center: float = 5.0,
        lane_width: float = 3.5,
        lane_count: int = 1,
    ) -> List[MarkingInstance]:
        """
        Place stop bars at intersection approaches.

        Args:
            intersection_position: Intersection center
            approach_angles: Angles of approaching roads
            distance_from_center: Distance from intersection center
            lane_width: Width of each lane
            lane_count: Number of lanes

        Returns:
            List of MarkingInstance
        """
        markings = []
        stop_bar_spec = self.catalog.get("STOP-BAR")
        x, y, z = intersection_position

        if not stop_bar_spec:
            return markings

        for angle in approach_angles:
            rad = math.radians(angle)
            bar_x = x + distance_from_center * math.cos(rad)
            bar_y = y + distance_from_center * math.sin(rad)

            # Stop bar perpendicular to approach
            perp_angle = angle + 90
            perp_rad = math.radians(perp_angle)

            bar_width = lane_width * lane_count
            half_width = bar_width / 2

            start = (
                bar_x - half_width * math.cos(perp_rad),
                bar_y - half_width * math.sin(perp_rad),
            )
            end = (
                bar_x + half_width * math.cos(perp_rad),
                bar_y + half_width * math.sin(perp_rad),
            )

            markings.append(MarkingInstance(
                instance_id=f"stopbar_{angle:.0f}",
                spec=stop_bar_spec,
                start=start,
                end=end,
                rotation=perp_angle,
            ))

        return markings

    def place_lane_arrows(
        self,
        lane_centerline: List[Tuple[float, float]],
        arrow_type: str = "ARROW-STRAIGHT",
        spacing: float = 30.0,
    ) -> List[MarkingInstance]:
        """
        Place lane arrows along lane.

        Args:
            lane_centerline: List of (x, y) points
            arrow_type: Arrow marking ID
            spacing: Distance between arrows

        Returns:
            List of MarkingInstance
        """
        markings = []
        arrow_spec = self.catalog.get(arrow_type)

        if not arrow_spec:
            return markings

        distance = 0.0
        next_arrow = spacing / 2

        for i in range(len(lane_centerline) - 1):
            start = lane_centerline[i]
            end = lane_centerline[i + 1]

            dx = end[0] - start[0]
            dy = end[1] - start[1]
            length = math.sqrt(dx * dx + dy * dy)
            angle = math.degrees(math.atan2(dy, dx))

            segment_start = distance
            segment_end = distance + length

            while next_arrow < segment_end:
                t = (next_arrow - segment_start) / length
                x = start[0] + (end[0] - start[0]) * t
                y = start[1] + (end[1] - start[1]) * t

                markings.append(MarkingInstance(
                    instance_id=f"arrow_{len(markings)}",
                    spec=arrow_spec,
                    start=(x - 0.5, y - 0.5),
                    end=(x + 0.5, y + 0.5),
                    rotation=angle,
                ))

                next_arrow += spacing

            distance += length

        return markings


def create_marking_placer() -> MarkingPlacer:
    """Convenience function to create marking placer."""
    return MarkingPlacer()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "MarkingColor",
    "MarkingType",
    "MarkingMaterial",
    "MarkingSpec",
    "MarkingInstance",
    "CrosswalkGeometry",
    "LANE_LINE_MARKINGS",
    "CROSSWALK_MARKINGS",
    "SYMBOL_MARKINGS",
    "SPECIAL_MARKINGS",
    "MARKING_CATALOG",
    "MarkingPlacer",
    "create_marking_placer",
]
