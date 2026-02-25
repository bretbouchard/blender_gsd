"""
MSG-1998 Lane Markings System

Generates road markings:
- Center lines (yellow, double)
- Lane dividers (white, dashed)
- Edge lines (white, solid)
- Crosswalks
- Stop lines
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
import math


class MarkingType(Enum):
    """Types of road markings."""
    CENTER_DOUBLE_YELLOW = "center_double_yellow"   # Double yellow center line
    CENTER_SINGLE_YELLOW = "center_single_yellow"   # Single yellow (one-way)
    LANE_DASHED_WHITE = "lane_dashed_white"         # Dashed lane divider
    LANE_SOLID_WHITE = "lane_solid_white"           # Solid lane divider
    EDGE_SOLID_WHITE = "edge_solid_white"           # Edge line
    CROSSWALK = "crosswalk"                         # Zebra crosswalk
    STOP_LINE = "stop_line"                         # Stop line at intersection
    TURN_ARROW = "turn_arrow"                       # Turn arrow marking
    PEDESTRIAN_XING = "pedestrian_xing"             # Pedestrian crossing indicator


@dataclass
class MarkingSpec:
    """Specification for a road marking."""
    marking_type: MarkingType
    color: Tuple[float, float, float, float]  # RGBA
    width: float  # meters
    length: float  # meters (for solid markings)
    dash_length: float  # meters (for dashed markings)
    gap_length: float  # meters (for dashed markings)
    thickness: float  # Paint thickness in meters

    @property
    def is_dashed(self) -> bool:
        """Check if marking is dashed."""
        return self.dash_length > 0


# Standard NYC 1998 marking specifications
MARKING_SPECS: Dict[MarkingType, MarkingSpec] = {
    MarkingType.CENTER_DOUBLE_YELLOW: MarkingSpec(
        marking_type=MarkingType.CENTER_DOUBLE_YELLOW,
        color=(0.9, 0.8, 0.0, 1.0),  # Yellow
        width=0.10,
        length=0.0,  # Continuous
        dash_length=0.0,
        gap_length=0.0,
        thickness=0.003,
    ),
    MarkingType.CENTER_SINGLE_YELLOW: MarkingSpec(
        marking_type=MarkingType.CENTER_SINGLE_YELLOW,
        color=(0.9, 0.8, 0.0, 1.0),
        width=0.10,
        length=0.0,
        dash_length=0.0,
        gap_length=0.0,
        thickness=0.003,
    ),
    MarkingType.LANE_DASHED_WHITE: MarkingSpec(
        marking_type=MarkingType.LANE_DASHED_WHITE,
        color=(1.0, 1.0, 1.0, 1.0),  # White
        width=0.10,
        length=0.0,
        dash_length=3.0,  # 3m dashes
        gap_length=9.0,   # 9m gaps (standard 1:3 ratio)
        thickness=0.003,
    ),
    MarkingType.LANE_SOLID_WHITE: MarkingSpec(
        marking_type=MarkingType.LANE_SOLID_WHITE,
        color=(1.0, 1.0, 1.0, 1.0),
        width=0.15,
        length=0.0,
        dash_length=0.0,
        gap_length=0.0,
        thickness=0.003,
    ),
    MarkingType.EDGE_SOLID_WHITE: MarkingSpec(
        marking_type=MarkingType.EDGE_SOLID_WHITE,
        color=(0.95, 0.95, 0.95, 1.0),
        width=0.15,
        length=0.0,
        dash_length=0.0,
        gap_length=0.0,
        thickness=0.003,
    ),
    MarkingType.CROSSWALK: MarkingSpec(
        marking_type=MarkingType.CROSSWALK,
        color=(1.0, 1.0, 1.0, 1.0),
        width=0.40,  # 40cm stripes
        length=0.0,
        dash_length=0.40,
        gap_length=0.60,  # 40cm stripe, 60cm gap
        thickness=0.005,
    ),
    MarkingType.STOP_LINE: MarkingSpec(
        marking_type=MarkingType.STOP_LINE,
        color=(1.0, 1.0, 1.0, 1.0),
        width=0.60,  # Thick stop line
        length=0.0,
        dash_length=0.0,
        gap_length=0.0,
        thickness=0.005,
    ),
}


@dataclass
class MarkingGeometry:
    """Generated geometry for a road marking."""
    marking_type: MarkingType
    vertices: List[Tuple[float, float, float]] = field(default_factory=list)
    faces: List[Tuple[int, ...]] = field(default_factory=list)
    material_index: int = 0


class MarkingBuilder:
    """
    Builds road marking geometry.

    Generates painted line markings as thin 3D geometry
    positioned slightly above the road surface.
    """

    def __init__(
        self,
        default_thickness: float = 0.003,
        z_offset: float = 0.01,  # Slightly above road to avoid z-fighting
    ):
        """
        Initialize marking builder.

        Args:
            default_thickness: Paint thickness in meters
            z_offset: Height above road surface
        """
        self.default_thickness = default_thickness
        self.z_offset = z_offset

    def build_line_marking(
        self,
        vertices: List[Tuple[float, float, float]],
        marking_type: MarkingType,
        offset: float = 0.0,  # Lateral offset from center
        road_name: str = "road",
    ) -> MarkingGeometry:
        """
        Build a line marking along a road centerline.

        Args:
            vertices: Road centerline vertices
            marking_type: Type of marking to build
            offset: Lateral offset from centerline (meters)
            road_name: Road name for identification

        Returns:
            MarkingGeometry with marking mesh data
        """
        spec = MARKING_SPECS.get(marking_type)
        if not spec:
            raise ValueError(f"Unknown marking type: {marking_type}")

        geometry = MarkingGeometry(marking_type=marking_type)

        if len(vertices) < 2:
            return geometry

        if spec.is_dashed:
            return self._build_dashed_line(vertices, spec, offset, road_name)
        else:
            return self._build_solid_line(vertices, spec, offset, road_name)

    def _build_solid_line(
        self,
        vertices: List[Tuple[float, float, float]],
        spec: MarkingSpec,
        offset: float,
        road_name: str,
    ) -> MarkingGeometry:
        """Build a solid continuous line marking."""
        geometry = MarkingGeometry(marking_type=spec.marking_type)
        half_width = spec.width / 2

        # Generate vertices along the line
        for i, (x, y, z) in enumerate(vertices):
            # Calculate direction and perpendicular
            if i == 0:
                dx = vertices[1][0] - x
                dy = vertices[1][1] - y
            elif i == len(vertices) - 1:
                dx = x - vertices[-2][0]
                dy = y - vertices[-2][1]
            else:
                dx1 = vertices[i + 1][0] - x
                dy1 = vertices[i + 1][1] - y
                dx2 = x - vertices[i - 1][0]
                dy2 = y - vertices[i - 1][1]
                dx = (dx1 + dx2) / 2
                dy = (dy1 + dy2) / 2

            length = math.sqrt(dx * dx + dy * dy)
            if length < 0.001:
                dx, dy = 1.0, 0.0
            else:
                dx /= length
                dy /= length

            # Perpendicular
            px, py = -dy, dx

            # Apply offset from centerline
            offset_x = offset * px
            offset_y = offset * py

            # Line position with offset
            line_z = z + self.z_offset

            # Left and right vertices
            geometry.vertices.append((
                x + offset_x - px * half_width,
                y + offset_y - py * half_width,
                line_z,
            ))
            geometry.vertices.append((
                x + offset_x + px * half_width,
                y + offset_y + py * half_width,
                line_z + spec.thickness,
            ))

        # Generate faces
        n_cross = len(vertices)
        for i in range(n_cross - 1):
            v0 = i * 2
            v1 = i * 2 + 1
            v2 = (i + 1) * 2 + 1
            v3 = (i + 1) * 2
            geometry.faces.append((v0, v1, v2, v3))

        return geometry

    def _build_dashed_line(
        self,
        vertices: List[Tuple[float, float, float]],
        spec: MarkingSpec,
        offset: float,
        road_name: str,
    ) -> MarkingGeometry:
        """Build a dashed line marking."""
        geometry = MarkingGeometry(marking_type=spec.marking_type)

        # Calculate total road length and segment positions
        total_length = 0.0
        segments = [(0.0, vertices[0])]  # (cumulative_length, position)

        for i in range(1, len(vertices)):
            dx = vertices[i][0] - vertices[i - 1][0]
            dy = vertices[i][1] - vertices[i - 1][1]
            seg_length = math.sqrt(dx * dx + dy * dy)
            total_length += seg_length
            segments.append((total_length, vertices[i]))

        # Calculate dash positions
        dash_positions = []
        pos = 0.0
        while pos < total_length:
            dash_positions.append(pos)
            pos += spec.dash_length + spec.gap_length

        # Generate geometry for each dash
        vertex_offset = 0
        for dash_start in dash_positions:
            dash_end = min(dash_start + spec.dash_length, total_length)

            # Find interpolated positions for dash start/end
            start_pos = self._interpolate_position(segments, dash_start)
            end_pos = self._interpolate_position(segments, dash_end)

            if start_pos is None or end_pos is None:
                continue

            # Generate dash geometry (simple rectangle)
            dash_verts, dash_faces = self._create_dash(
                start_pos, end_pos, spec, offset
            )

            # Offset face indices
            for face in dash_faces:
                geometry.faces.append(tuple(v + vertex_offset for v in face))

            geometry.vertices.extend(dash_verts)
            vertex_offset += len(dash_verts)

        return geometry

    def _interpolate_position(
        self,
        segments: List[Tuple[float, Tuple[float, float, float]]],
        target_length: float,
    ) -> Optional[Tuple[Tuple[float, float, float], float, float]]:
        """
        Interpolate position at a given length along the road.

        Returns (position, direction_x, direction_y) or None if out of range.
        """
        if target_length < 0 or target_length > segments[-1][0]:
            return None

        # Find segment containing target length
        for i in range(1, len(segments)):
            seg_start_len, seg_start_pos = segments[i - 1]
            seg_end_len, seg_end_pos = segments[i]

            if seg_start_len <= target_length <= seg_end_len:
                # Interpolate
                seg_length = seg_end_len - seg_start_len
                if seg_length < 0.001:
                    t = 0.0
                else:
                    t = (target_length - seg_start_len) / seg_length

                x = seg_start_pos[0] + t * (seg_end_pos[0] - seg_start_pos[0])
                y = seg_start_pos[1] + t * (seg_end_pos[1] - seg_start_pos[1])
                z = seg_start_pos[2] + t * (seg_end_pos[2] - seg_start_pos[2])

                # Direction
                dx = seg_end_pos[0] - seg_start_pos[0]
                dy = seg_end_pos[1] - seg_start_pos[1]
                length = math.sqrt(dx * dx + dy * dy)
                if length < 0.001:
                    dx, dy = 1.0, 0.0
                else:
                    dx /= length
                    dy /= length

                return ((x, y, z), dx, dy)

        return None

    def _create_dash(
        self,
        start_info: Tuple[Tuple[float, float, float], float, float],
        end_info: Tuple[Tuple[float, float, float], float, float],
        spec: MarkingSpec,
        offset: float,
    ) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, ...]]]:
        """Create a single dash geometry."""
        (sx, sy, sz), sdx, sdy = start_info
        (ex, ey, ez), edx, edy = end_info

        half_width = spec.width / 2

        # Perpendicular directions
        spx, spy = -sdy, sdx
        epx, epy = -edy, edx

        # Apply offset
        sox = offset * spx
        soy = offset * spy
        eox = offset * epx
        eoy = offset * epy

        # Z position
        sz += self.z_offset
        ez += self.z_offset

        vertices = [
            # Start left
            (sx + sox - spx * half_width, sy + soy - spy * half_width, sz),
            # Start right
            (sx + sox + spx * half_width, sy + soy + spy * half_width, sz + spec.thickness),
            # End right
            (ex + eox + epx * half_width, ey + eoy + epy * half_width, ez + spec.thickness),
            # End left
            (ex + eox - epx * half_width, ey + eoy - epy * half_width, ez),
        ]

        faces = [(0, 1, 2, 3)]

        return vertices, faces


class CrosswalkBuilder:
    """
    Builds crosswalk (zebra crossing) geometry.

    Creates striped pedestrian crossing markings.
    """

    def __init__(
        self,
        stripe_width: float = 0.40,
        stripe_gap: float = 0.60,
        crosswalk_width: float = 3.0,
        thickness: float = 0.005,
    ):
        """
        Initialize crosswalk builder.

        Args:
            stripe_width: Width of each white stripe
            stripe_gap: Gap between stripes
            crosswalk_width: Total width of crossing
            thickness: Paint thickness
        """
        self.stripe_width = stripe_width
        self.stripe_gap = stripe_gap
        self.crosswalk_width = crosswalk_width
        self.thickness = thickness

    def build(
        self,
        position: Tuple[float, float, float],
        direction: float,
        length: float,
        width: Optional[float] = None,
    ) -> MarkingGeometry:
        """
        Build crosswalk geometry.

        Args:
            position: Center position of crosswalk
            direction: Direction perpendicular to road (radians)
            length: Length along road (stripe count determined by this)
            width: Width across road (uses default if None)

        Returns:
            MarkingGeometry with crosswalk mesh data
        """
        geometry = MarkingGeometry(marking_type=MarkingType.CROSSWALK)
        width = width or self.crosswalk_width

        # Direction vectors
        # Direction is perpendicular to road, so stripes go along road direction
        stripe_dir = direction + math.pi / 2  # Along road
        road_dir = direction  # Across road

        dx = math.cos(stripe_dir)
        dy = math.sin(stripe_dir)
        px = math.cos(road_dir)
        py = math.sin(road_dir)

        cx, cy, cz = position
        cz += 0.01  # Z offset

        # Calculate number of stripes
        stripe_pitch = self.stripe_width + self.stripe_gap
        num_stripes = int(length / stripe_pitch)

        # Generate stripes
        vertex_offset = 0
        half_length = length / 2
        half_width = width / 2

        for i in range(num_stripes):
            # Stripe center position along road
            stripe_center = -half_length + i * stripe_pitch + self.stripe_width / 2

            # Stripe start and end along road direction
            stripe_start = stripe_center - self.stripe_width / 2
            stripe_end = stripe_center + self.stripe_width / 2

            # Vertices
            sx = cx + dx * stripe_start
            sy = cy + dy * stripe_start
            ex = cx + dx * stripe_end
            ey = cy + dy * stripe_end

            geometry.vertices.extend([
                # Start left (across road)
                (sx - px * half_width, sy - py * half_width, cz),
                # Start right
                (sx + px * half_width, sy + py * half_width, cz + self.thickness),
                # End right
                (ex + px * half_width, ey + py * half_width, cz + self.thickness),
                # End left
                (ex - px * half_width, ey - py * half_width, cz),
            ])

            geometry.faces.append((
                vertex_offset,
                vertex_offset + 1,
                vertex_offset + 2,
                vertex_offset + 3,
            ))
            vertex_offset += 4

        return geometry


class RoadMarkingGenerator:
    """
    High-level generator that creates all markings for a road.

    Determines appropriate markings based on road type and
    generates all necessary geometry.
    """

    def __init__(
        self,
        marking_builder: Optional[MarkingBuilder] = None,
        crosswalk_builder: Optional[CrosswalkBuilder] = None,
    ):
        """
        Initialize generator.

        Args:
            marking_builder: Custom marking builder
            crosswalk_builder: Custom crosswalk builder
        """
        self.marking_builder = marking_builder or MarkingBuilder()
        self.crosswalk_builder = crosswalk_builder or CrosswalkBuilder()

    def generate_markings(
        self,
        road_vertices: List[Tuple[float, float, float]],
        road_width: float,
        lanes: int,
        is_oneway: bool = False,
        marking_detail: str = "full",  # "full", "basic", "minimal", "none"
        road_name: str = "road",
    ) -> List[MarkingGeometry]:
        """
        Generate all markings for a road segment.

        Args:
            road_vertices: Road centerline vertices
            road_width: Road width in meters
            lanes: Number of lanes
            is_oneway: Whether road is one-way
            marking_detail: Level of marking detail
            road_name: Road name for identification

        Returns:
            List of MarkingGeometry objects
        """
        if marking_detail == "none" or len(road_vertices) < 2:
            return []

        markings = []
        half_width = road_width / 2

        # Center line
        if not is_oneway:
            # Double yellow center line for two-way roads
            center_offset = 0.1  # Slight offset for double line
            markings.append(self.marking_builder.build_line_marking(
                vertices=road_vertices,
                marking_type=MarkingType.CENTER_DOUBLE_YELLOW,
                offset=-center_offset,
                road_name=road_name,
            ))
            markings.append(self.marking_builder.build_line_marking(
                vertices=road_vertices,
                marking_type=MarkingType.CENTER_DOUBLE_YELLOW,
                offset=center_offset,
                road_name=road_name,
            ))
        else:
            # Single yellow for one-way left edge
            markings.append(self.marking_builder.build_line_marking(
                vertices=road_vertices,
                marking_type=MarkingType.CENTER_SINGLE_YELLOW,
                offset=-half_width + 0.2,
                road_name=road_name,
            ))

        # Lane dividers
        if lanes > 1 and marking_detail in ("full", "basic"):
            # Calculate lane positions
            lane_width = road_width / lanes
            for lane in range(1, lanes):
                offset = -half_width + lane * lane_width
                markings.append(self.marking_builder.build_line_marking(
                    vertices=road_vertices,
                    marking_type=MarkingType.LANE_DASHED_WHITE,
                    offset=offset,
                    road_name=road_name,
                ))

        # Edge lines
        if marking_detail == "full":
            # Left edge
            markings.append(self.marking_builder.build_line_marking(
                vertices=road_vertices,
                marking_type=MarkingType.EDGE_SOLID_WHITE,
                offset=-half_width + 0.2,
                road_name=road_name,
            ))
            # Right edge
            markings.append(self.marking_builder.build_line_marking(
                vertices=road_vertices,
                marking_type=MarkingType.EDGE_SOLID_WHITE,
                offset=half_width - 0.2,
                road_name=road_name,
            ))

        return [m for m in markings if len(m.vertices) > 0]


__all__ = [
    "MarkingType",
    "MarkingSpec",
    "MARKING_SPECS",
    "MarkingGeometry",
    "MarkingBuilder",
    "CrosswalkBuilder",
    "RoadMarkingGenerator",
]
