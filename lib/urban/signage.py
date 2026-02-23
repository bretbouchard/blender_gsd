"""
Street Sign Library

MUTCD-compliant street sign system for road networks.
Provides regulatory, warning, and guide signs.

Implements REQ-UR-04: Street Sign Library.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum
import math


class SignCategory(Enum):
    """MUTCD sign categories."""
    REGULATORY = "regulatory"
    WARNING = "warning"
    GUIDE = "guide"
    CONSTRUCTION = "construction"
    RECREATION = "recreation"


class SignShape(Enum):
    """Sign shape types."""
    CIRCLE = "circle"
    TRIANGLE = "triangle"
    RECTANGLE = "rectangle"
    OCTAGON = "octagon"
    DIAMOND = "diamond"
    PENTAGON = "pentagon"
    SHIELD = "shield"
    CUSTOM = "custom"


class SignPurpose(Enum):
    """Sign functional purpose."""
    STOP = "stop"
    YIELD = "yield"
    SPEED_LIMIT = "speed_limit"
    NO_ENTRY = "no_entry"
    ONE_WAY = "one_way"
    DO_NOT_ENTER = "do_not_enter"
    TURN_PROHIBITION = "turn_prohibition"
    PARKING = "parking"
    PEDESTRIAN = "pedestrian"
    SCHOOL = "school"
    CURVE = "curve"
    INTERSECTION = "intersection"
    MERGE = "merge"
    LANE_END = "lane_end"
    STREET_NAME = "street_name"
    DESTINATION = "destination"
    EXIT = "exit"
    DISTANCE = "distance"
    ROUTE_MARKER = "route_marker"


@dataclass
class SignSpec:
    """
    Sign specification.

    Attributes:
        sign_id: Unique sign identifier
        name: Sign name
        category: MUTCD category
        shape: Sign shape
        purpose: Functional purpose
        width: Sign width in meters
        height: Sign height in meters
        background_color: Background color (hex or name)
        text_color: Text/foreground color
        border_color: Border color
        text_content: Text to display
        font_size: Font size relative to sign height
        has_border: Whether sign has border
        is_reflective: Whether sign is reflective
        mounting_height: Mounting height in meters
        offset_from_road: Lateral offset from road in meters
        is_double_sided: Whether sign is double-sided
    """
    sign_id: str = ""
    name: str = ""
    category: str = "regulatory"
    shape: str = "rectangle"
    purpose: str = "street_name"
    width: float = 0.6
    height: float = 0.45
    background_color: str = "#FFFFFF"
    text_color: str = "#000000"
    border_color: str = "#000000"
    text_content: str = ""
    font_size: float = 0.6
    has_border: bool = True
    is_reflective: bool = True
    mounting_height: float = 2.1
    offset_from_road: float = 0.6
    is_double_sided: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sign_id": self.sign_id,
            "name": self.name,
            "category": self.category,
            "shape": self.shape,
            "purpose": self.purpose,
            "width": self.width,
            "height": self.height,
            "background_color": self.background_color,
            "text_color": self.text_color,
            "border_color": self.border_color,
            "text_content": self.text_content,
            "font_size": self.font_size,
            "has_border": self.has_border,
            "is_reflective": self.is_reflective,
            "mounting_height": self.mounting_height,
            "offset_from_road": self.offset_from_road,
            "is_double_sided": self.is_double_sided,
        }


@dataclass
class SignInstance:
    """
    Sign placement instance.

    Attributes:
        instance_id: Unique instance identifier
        sign_spec: Sign specification
        position: Position (x, y, z)
        rotation: Rotation angle in degrees
        direction: Direction sign faces in degrees
        pole_type: Type of mounting pole
        is_double_sided: Whether sign is double-sided
    """
    instance_id: str = ""
    sign_spec: Optional[SignSpec] = None
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: float = 0.0
    direction: float = 0.0
    pole_type: str = "single"
    is_double_sided: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "instance_id": self.instance_id,
            "sign_spec": self.sign_spec.to_dict() if self.sign_spec else None,
            "position": list(self.position),
            "rotation": self.rotation,
            "direction": self.direction,
            "pole_type": self.pole_type,
            "is_double_sided": self.is_double_sided,
        }


# =============================================================================
# MUTCD STANDARD SIGNS
# =============================================================================

REGULATORY_SIGNS: Dict[str, SignSpec] = {
    # R1 Series - Stop and Yield
    "R1-1": SignSpec(
        sign_id="R1-1",
        name="STOP",
        category="regulatory",
        shape="octagon",
        purpose="stop",
        width=0.75,
        height=0.75,
        background_color="#CC0000",
        text_color="#FFFFFF",
        border_color="#FFFFFF",
        text_content="STOP",
        font_size=0.45,
        mounting_height=1.5,
    ),
    "R1-2": SignSpec(
        sign_id="R1-2",
        name="YIELD",
        category="regulatory",
        shape="triangle",
        purpose="yield",
        width=0.9,
        height=0.75,
        background_color="#FFFFFF",
        text_color="#CC0000",
        border_color="#CC0000",
        text_content="YIELD",
        font_size=0.35,
        mounting_height=1.8,
    ),

    # R2 Series - Speed Limit
    "R2-1": SignSpec(
        sign_id="R2-1",
        name="Speed Limit",
        category="regulatory",
        shape="rectangle",
        purpose="speed_limit",
        width=0.6,
        height=0.75,
        background_color="#FFFFFF",
        text_color="#000000",
        border_color="#000000",
        text_content="SPEED LIMIT\n{speed}",
        font_size=0.4,
        mounting_height=2.1,
    ),

    # R3 Series - Movement Prohibition
    "R3-1": SignSpec(
        sign_id="R3-1",
        name="No Right Turn",
        category="regulatory",
        shape="circle",
        purpose="turn_prohibition",
        width=0.6,
        height=0.6,
        background_color="#FFFFFF",
        text_color="#CC0000",
        border_color="#CC0000",
        text_content="",
        font_size=0.0,
        mounting_height=2.1,
    ),
    "R3-2": SignSpec(
        sign_id="R3-2",
        name="No Left Turn",
        category="regulatory",
        shape="circle",
        purpose="turn_prohibition",
        width=0.6,
        height=0.6,
        background_color="#FFFFFF",
        text_color="#CC0000",
        border_color="#CC0000",
        text_content="",
        font_size=0.0,
        mounting_height=2.1,
    ),
    "R3-3": SignSpec(
        sign_id="R3-3",
        name="No U-Turn",
        category="regulatory",
        shape="circle",
        purpose="turn_prohibition",
        width=0.6,
        height=0.6,
        background_color="#FFFFFF",
        text_color="#CC0000",
        border_color="#CC0000",
        text_content="",
        font_size=0.0,
        mounting_height=2.1,
    ),

    # R4 Series - Lane Usage
    "R4-1": SignSpec(
        sign_id="R4-1",
        name="Do Not Pass",
        category="regulatory",
        shape="rectangle",
        purpose="regulatory",
        width=0.6,
        height=0.75,
        background_color="#FFFFFF",
        text_color="#000000",
        border_color="#000000",
        text_content="DO NOT\nPASS",
        font_size=0.35,
        mounting_height=2.1,
    ),

    # R5 Series - Exclude
    "R5-1": SignSpec(
        sign_id="R5-1",
        name="Do Not Enter",
        category="regulatory",
        shape="circle",
        purpose="do_not_enter",
        width=0.75,
        height=0.75,
        background_color="#FFFFFF",
        text_color="#CC0000",
        border_color="#CC0000",
        text_content="",
        font_size=0.0,
        mounting_height=1.8,
    ),

    # R6 Series - One Way
    "R6-1": SignSpec(
        sign_id="R6-1",
        name="One Way",
        category="regulatory",
        shape="rectangle",
        purpose="one_way",
        width=0.6,
        height=0.9,
        background_color="#FFFFFF",
        text_color="#000000",
        border_color="#000000",
        text_content="ONE WAY",
        font_size=0.35,
        mounting_height=2.1,
        is_double_sided=True,
    ),

    # R7 Series - Parking
    "R7-1": SignSpec(
        sign_id="R7-1",
        name="No Parking",
        category="regulatory",
        shape="rectangle",
        purpose="parking",
        width=0.45,
        height=0.6,
        background_color="#FFFFFF",
        text_color="#CC0000",
        border_color="#CC0000",
        text_content="NO\nPARKING",
        font_size=0.3,
        mounting_height=1.5,
    ),
    "R7-2": SignSpec(
        sign_id="R7-2",
        name="No Parking Any Time",
        category="regulatory",
        shape="rectangle",
        purpose="parking",
        width=0.45,
        height=0.75,
        background_color="#FFFFFF",
        text_color="#CC0000",
        border_color="#CC0000",
        text_content="NO PARKING\nANY TIME",
        font_size=0.25,
        mounting_height=1.5,
    ),

    # R10 Series - Traffic Signals
    "R10-1": SignSpec(
        sign_id="R10-1",
        name="Left on Green Arrow Only",
        category="regulatory",
        shape="rectangle",
        purpose="regulatory",
        width=0.6,
        height=0.45,
        background_color="#FFFFFF",
        text_color="#000000",
        border_color="#000000",
        text_content="LEFT ON\nGREEN ARROW\nONLY",
        font_size=0.25,
        mounting_height=2.1,
    ),
}

WARNING_SIGNS: Dict[str, SignSpec] = {
    # W1 Series - Turn and Curve
    "W1-1": SignSpec(
        sign_id="W1-1",
        name="Turn",
        category="warning",
        shape="diamond",
        purpose="curve",
        width=0.75,
        height=0.75,
        background_color="#FFCC00",
        text_color="#000000",
        border_color="#000000",
        text_content="",
        font_size=0.0,
        mounting_height=1.5,
    ),
    "W1-2": SignSpec(
        sign_id="W1-2",
        name="Curve",
        category="warning",
        shape="diamond",
        purpose="curve",
        width=0.75,
        height=0.75,
        background_color="#FFCC00",
        text_color="#000000",
        border_color="#000000",
        text_content="",
        font_size=0.0,
        mounting_height=1.5,
    ),
    "W1-3": SignSpec(
        sign_id="W1-3",
        name="Reverse Turn",
        category="warning",
        shape="diamond",
        purpose="curve",
        width=0.75,
        height=0.75,
        background_color="#FFCC00",
        text_color="#000000",
        border_color="#000000",
        text_content="",
        font_size=0.0,
        mounting_height=1.5,
    ),
    "W1-4": SignSpec(
        sign_id="W1-4",
        name="Winding Road",
        category="warning",
        shape="diamond",
        purpose="curve",
        width=0.75,
        height=0.75,
        background_color="#FFCC00",
        text_color="#000000",
        border_color="#000000",
        text_content="",
        font_size=0.0,
        mounting_height=1.5,
    ),

    # W2 Series - Intersection
    "W2-1": SignSpec(
        sign_id="W2-1",
        name="Cross Road",
        category="warning",
        shape="diamond",
        purpose="intersection",
        width=0.75,
        height=0.75,
        background_color="#FFCC00",
        text_color="#000000",
        border_color="#000000",
        text_content="",
        font_size=0.0,
        mounting_height=1.5,
    ),
    "W2-2": SignSpec(
        sign_id="W2-2",
        name="Side Road",
        category="warning",
        shape="diamond",
        purpose="intersection",
        width=0.75,
        height=0.75,
        background_color="#FFCC00",
        text_color="#000000",
        border_color="#000000",
        text_content="",
        font_size=0.0,
        mounting_height=1.5,
    ),
    "W2-3": SignSpec(
        sign_id="W2-3",
        name="T Intersection",
        category="warning",
        shape="diamond",
        purpose="intersection",
        width=0.75,
        height=0.75,
        background_color="#FFCC00",
        text_color="#000000",
        border_color="#000000",
        text_content="",
        font_size=0.0,
        mounting_height=1.5,
    ),
    "W2-4": SignSpec(
        sign_id="W2-4",
        name="Y Intersection",
        category="warning",
        shape="diamond",
        purpose="intersection",
        width=0.75,
        height=0.75,
        background_color="#FFCC00",
        text_color="#000000",
        border_color="#000000",
        text_content="",
        font_size=0.0,
        mounting_height=1.5,
    ),
    "W2-5": SignSpec(
        sign_id="W2-5",
        name="Roundabout",
        category="warning",
        shape="diamond",
        purpose="intersection",
        width=0.75,
        height=0.75,
        background_color="#FFCC00",
        text_color="#000000",
        border_color="#000000",
        text_content="",
        font_size=0.0,
        mounting_height=1.5,
    ),

    # W3 Series - Advance Traffic Control
    "W3-1": SignSpec(
        sign_id="W3-1",
        name="Stop Ahead",
        category="warning",
        shape="diamond",
        purpose="regulatory",
        width=0.75,
        height=0.75,
        background_color="#FFCC00",
        text_color="#000000",
        border_color="#000000",
        text_content="",
        font_size=0.0,
        mounting_height=1.5,
    ),
    "W3-2": SignSpec(
        sign_id="W3-2",
        name="Yield Ahead",
        category="warning",
        shape="diamond",
        purpose="regulatory",
        width=0.75,
        height=0.75,
        background_color="#FFCC00",
        text_color="#000000",
        border_color="#000000",
        text_content="",
        font_size=0.0,
        mounting_height=1.5,
    ),
    "W3-3": SignSpec(
        sign_id="W3-3",
        name="Signal Ahead",
        category="warning",
        shape="diamond",
        purpose="regulatory",
        width=0.75,
        height=0.75,
        background_color="#FFCC00",
        text_color="#000000",
        border_color="#000000",
        text_content="",
        font_size=0.0,
        mounting_height=1.5,
    ),

    # W4 Series - Merge
    "W4-1": SignSpec(
        sign_id="W4-1",
        name="Merge",
        category="warning",
        shape="diamond",
        purpose="merge",
        width=0.75,
        height=0.75,
        background_color="#FFCC00",
        text_color="#000000",
        border_color="#000000",
        text_content="",
        font_size=0.0,
        mounting_height=1.5,
    ),
    "W4-2": SignSpec(
        sign_id="W4-2",
        name="Lane Ends",
        category="warning",
        shape="diamond",
        purpose="lane_end",
        width=0.75,
        height=0.75,
        background_color="#FFCC00",
        text_color="#000000",
        border_color="#000000",
        text_content="",
        font_size=0.0,
        mounting_height=1.5,
    ),

    # W6 Series - Divided Highway
    "W6-1": SignSpec(
        sign_id="W6-1",
        name="Divided Highway Begins",
        category="warning",
        shape="diamond",
        purpose="warning",
        width=0.75,
        height=0.75,
        background_color="#FFCC00",
        text_color="#000000",
        border_color="#000000",
        text_content="",
        font_size=0.0,
        mounting_height=1.5,
    ),
    "W6-2": SignSpec(
        sign_id="W6-2",
        name="Divided Highway Ends",
        category="warning",
        shape="diamond",
        purpose="warning",
        width=0.75,
        height=0.75,
        background_color="#FFCC00",
        text_color="#000000",
        border_color="#000000",
        text_content="",
        font_size=0.0,
        mounting_height=1.5,
    ),

    # W11 Series - Pedestrian and Bicycle
    "W11-1": SignSpec(
        sign_id="W11-1",
        name="Pedestrian Crossing",
        category="warning",
        shape="diamond",
        purpose="pedestrian",
        width=0.75,
        height=0.75,
        background_color="#FFCC00",
        text_color="#000000",
        border_color="#000000",
        text_content="",
        font_size=0.0,
        mounting_height=1.5,
    ),
    "W11-2": SignSpec(
        sign_id="W11-2",
        name="Bicycle Crossing",
        category="warning",
        shape="diamond",
        purpose="warning",
        width=0.75,
        height=0.75,
        background_color="#FFCC00",
        text_color="#000000",
        border_color="#000000",
        text_content="",
        font_size=0.0,
        mounting_height=1.5,
    ),

    # S1 Series - School
    "S1-1": SignSpec(
        sign_id="S1-1",
        name="School",
        category="warning",
        shape="pentagon",
        purpose="school",
        width=0.75,
        height=0.9,
        background_color="#FFCC00",
        text_color="#000000",
        border_color="#000000",
        text_content="",
        font_size=0.0,
        mounting_height=1.5,
    ),
}

GUIDE_SIGNS: Dict[str, SignSpec] = {
    # D3 Series - Street Name
    "D3-1": SignSpec(
        sign_id="D3-1",
        name="Street Name",
        category="guide",
        shape="rectangle",
        purpose="street_name",
        width=0.9,
        height=0.45,
        background_color="#006633",
        text_color="#FFFFFF",
        border_color="#FFFFFF",
        text_content="{street_name}",
        font_size=0.5,
        mounting_height=3.0,
        is_double_sided=True,
    ),

    # D1 Series - Route Markers
    "D1-1": SignSpec(
        sign_id="D1-1",
        name="Route Marker",
        category="guide",
        shape="shield",
        purpose="route_marker",
        width=0.45,
        height=0.45,
        background_color="#FFFFFF",
        text_color="#000000",
        border_color="#000000",
        text_content="{route}",
        font_size=0.4,
        mounting_height=2.1,
    ),
    "D1-2": SignSpec(
        sign_id="D1-2",
        name="Interstate Marker",
        category="guide",
        shape="shield",
        purpose="route_marker",
        width=0.6,
        height=0.6,
        background_color="#003399",
        text_color="#FFFFFF",
        border_color="#FF0000",
        text_content="{route}",
        font_size=0.35,
        mounting_height=2.1,
    ),
    "D1-3": SignSpec(
        sign_id="D1-3",
        name="US Route Marker",
        category="guide",
        shape="shield",
        purpose="route_marker",
        width=0.6,
        height=0.5,
        background_color="#FFFFFF",
        text_color="#000000",
        border_color="#000000",
        text_content="{route}",
        font_size=0.35,
        mounting_height=2.1,
    ),

    # I Series - Interstate Guide
    "I-1": SignSpec(
        sign_id="I-1",
        name="Interstate Exit",
        category="guide",
        shape="rectangle",
        purpose="exit",
        width=1.2,
        height=0.75,
        background_color="#006633",
        text_color="#FFFFFF",
        border_color="#FFFFFF",
        text_content="EXIT {number}",
        font_size=0.5,
        mounting_height=2.4,
    ),

    # D2 Series - Distance
    "D2-1": SignSpec(
        sign_id="D2-1",
        name="Distance",
        category="guide",
        shape="rectangle",
        purpose="distance",
        width=1.2,
        height=0.9,
        background_color="#006633",
        text_color="#FFFFFF",
        border_color="#FFFFFF",
        text_content="{destination}\n{distance} MI",
        font_size=0.35,
        mounting_height=2.4,
    ),
}


class SignLibrary:
    """
    Sign library with MUTCD-compliant signs.

    Usage:
        library = SignLibrary()
        sign = library.get_sign("R1-1")  # STOP sign
        all_regulatory = library.get_by_category("regulatory")
    """

    def __init__(self):
        """Initialize sign library with standard signs."""
        self._signs: Dict[str, SignSpec] = {}
        self._load_standard_signs()

    def _load_standard_signs(self) -> None:
        """Load MUTCD standard signs."""
        self._signs.update(REGULATORY_SIGNS)
        self._signs.update(WARNING_SIGNS)
        self._signs.update(GUIDE_SIGNS)

    def get_sign(self, sign_id: str) -> Optional[SignSpec]:
        """
        Get sign by ID.

        Args:
            sign_id: MUTCD sign identifier

        Returns:
            SignSpec or None
        """
        return self._signs.get(sign_id)

    def get_by_category(self, category: str) -> List[SignSpec]:
        """
        Get all signs in a category.

        Args:
            category: Sign category

        Returns:
            List of SignSpec
        """
        return [s for s in self._signs.values() if s.category == category]

    def get_by_purpose(self, purpose: str) -> List[SignSpec]:
        """
        Get all signs for a purpose.

        Args:
            purpose: Sign purpose

        Returns:
            List of SignSpec
        """
        return [s for s in self._signs.values() if s.purpose == purpose]

    def create_speed_limit_sign(self, speed: int) -> SignSpec:
        """
        Create speed limit sign with specified speed.

        Args:
            speed: Speed limit value

        Returns:
            SignSpec for speed limit
        """
        template = REGULATORY_SIGNS.get("R2-1")
        if template:
            spec = SignSpec(
                sign_id=f"R2-1-{speed}",
                name=f"Speed Limit {speed}",
                category=template.category,
                shape=template.shape,
                purpose=template.purpose,
                width=template.width,
                height=template.height,
                background_color=template.background_color,
                text_color=template.text_color,
                border_color=template.border_color,
                text_content=f"SPEED LIMIT\n{speed}",
                font_size=template.font_size,
                mounting_height=template.mounting_height,
            )
            return spec
        return SignSpec()

    def create_street_name_sign(self, street_name: str) -> SignSpec:
        """
        Create street name sign.

        Args:
            street_name: Street name text

        Returns:
            SignSpec for street name
        """
        template = GUIDE_SIGNS.get("D3-1")
        if template:
            spec = SignSpec(
                sign_id=f"D3-1-{street_name}",
                name=street_name,
                category=template.category,
                shape=template.shape,
                purpose=template.purpose,
                width=template.width,
                height=template.height,
                background_color=template.background_color,
                text_color=template.text_color,
                border_color=template.border_color,
                text_content=street_name,
                font_size=template.font_size,
                mounting_height=template.mounting_height,
                is_double_sided=template.is_double_sided,
            )
            return spec
        return SignSpec()

    def list_signs(self) -> List[str]:
        """Get list of all sign IDs."""
        return list(self._signs.keys())

    def to_json(self) -> Dict[str, Any]:
        """Export library to JSON."""
        return {
            "regulatory": {k: v.to_dict() for k, v in REGULATORY_SIGNS.items()},
            "warning": {k: v.to_dict() for k, v in WARNING_SIGNS.items()},
            "guide": {k: v.to_dict() for k, v in GUIDE_SIGNS.items()},
        }


class SignPlacer:
    """
    Places signs along road network.

    Usage:
        placer = SignPlacer(library)
        placements = placer.place_signs(network, intersections)
    """

    def __init__(self, library: Optional[SignLibrary] = None):
        """
        Initialize sign placer.

        Args:
            library: SignLibrary to use
        """
        self.library = library or SignLibrary()

    def place_signs_at_intersection(
        self,
        position: Tuple[float, float, float],
        intersection_type: str,
        road_names: List[str] = None,
        has_traffic_signal: bool = False,
    ) -> List[SignInstance]:
        """
        Place appropriate signs at intersection.

        Args:
            position: Intersection position
            intersection_type: Type of intersection
            road_names: Names of intersecting roads
            has_traffic_signal: Whether intersection has traffic signal

        Returns:
            List of SignInstance
        """
        signs = []
        base_x, base_y, base_z = position

        if intersection_type == "intersection_4way":
            # Stop signs if no traffic signal
            if not has_traffic_signal:
                for i, angle in enumerate([0, 90, 180, 270]):
                    rad = math.radians(angle)
                    x = base_x + 5 * math.cos(rad)
                    y = base_y + 5 * math.sin(rad)

                    stop_spec = self.library.get_sign("R1-1")
                    signs.append(SignInstance(
                        instance_id=f"stop_{i}",
                        sign_spec=stop_spec,
                        position=(x, y, base_z),
                        rotation=angle + 180,
                        direction=angle + 180,
                        pole_type="single",
                    ))

            # Street name signs
            if road_names:
                for i, name in enumerate(road_names[:2]):
                    angle = 0 if i == 0 else 90
                    rad = math.radians(angle)
                    x = base_x + 4 * math.cos(rad + 45)
                    y = base_y + 4 * math.sin(rad + 45)

                    name_spec = self.library.create_street_name_sign(name)
                    signs.append(SignInstance(
                        instance_id=f"street_{i}",
                        sign_spec=name_spec,
                        position=(x, y, base_z + 3.0),
                        rotation=angle,
                        direction=angle,
                        pole_type="mast_arm",
                        is_double_sided=True,
                    ))

        elif intersection_type == "intersection_3way":
            # Stop sign for terminating road
            if not has_traffic_signal:
                stop_spec = self.library.get_sign("R1-1")
                signs.append(SignInstance(
                    instance_id="stop_0",
                    sign_spec=stop_spec,
                    position=(base_x + 5, base_y, base_z),
                    rotation=180,
                    direction=180,
                    pole_type="single",
                ))

        elif intersection_type == "roundabout":
            # Yield signs at all approaches
            yield_spec = self.library.get_sign("R1-2")
            for i, angle in enumerate([0, 90, 180, 270]):
                rad = math.radians(angle)
                x = base_x + 10 * math.cos(rad)
                y = base_y + 10 * math.sin(rad)

                signs.append(SignInstance(
                    instance_id=f"yield_{i}",
                    sign_spec=yield_spec,
                    position=(x, y, base_z),
                    rotation=angle + 180,
                    direction=angle + 180,
                    pole_type="single",
                ))

        return signs

    def place_speed_limit_signs(
        self,
        road_segments: List[Tuple[Tuple[float, float], Tuple[float, float]]],
        speed_limit: int = 35,
        spacing: float = 500.0,
    ) -> List[SignInstance]:
        """
        Place speed limit signs along road.

        Args:
            road_segments: List of (start, end) tuples
            speed_limit: Speed limit value
            spacing: Distance between signs

        Returns:
            List of SignInstance
        """
        signs = []
        spec = self.library.create_speed_limit_sign(speed_limit)

        for i, (start, end) in enumerate(road_segments):
            if i % int(spacing / 50) == 0:  # Approximate spacing
                mid_x = (start[0] + end[0]) / 2
                mid_y = (start[1] + end[1]) / 2

                # Calculate direction
                dx = end[0] - start[0]
                dy = end[1] - start[1]
                angle = math.degrees(math.atan2(dy, dx))

                # Offset perpendicular to road
                perp_angle = angle + 90
                offset = 3 * math.cos(math.radians(perp_angle)), 3 * math.sin(math.radians(perp_angle))

                signs.append(SignInstance(
                    instance_id=f"speed_{len(signs)}",
                    sign_spec=spec,
                    position=(mid_x + offset[0], mid_y + offset[1], 0),
                    rotation=angle,
                    direction=angle,
                    pole_type="single",
                ))

        return signs


def create_sign_library() -> SignLibrary:
    """Convenience function to create sign library."""
    return SignLibrary()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "SignCategory",
    "SignShape",
    "SignPurpose",
    "SignSpec",
    "SignInstance",
    "REGULATORY_SIGNS",
    "WARNING_SIGNS",
    "GUIDE_SIGNS",
    "SignLibrary",
    "SignPlacer",
    "create_sign_library",
]
