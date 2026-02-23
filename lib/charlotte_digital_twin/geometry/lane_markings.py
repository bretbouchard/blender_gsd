"""
Lane Marking Generator

Generates road lane markings including:
- Dashed center lines
- Solid edge lines
- Turn arrows
- Exit/merge arrows
- Crosswalks
- Stop lines

Uses procedural geometry and decal projection for realistic paint appearance.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
import math

try:
    import bpy
    import bmesh
    from bpy.types import Object, Mesh, Collection
    from mathutils import Vector, Matrix
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Object = Any
    Mesh = Any
    Collection = Any
    Vector = Any
    Matrix = Any


class MarkingType(Enum):
    """Types of road markings."""
    DASHED_LINE = "dashed"
    SOLID_LINE = "solid"
    DOUBLE_SOLID = "double_solid"
    DOUBLE_DASHED = "double_dashed"
    SOLID_DASH = "solid_dash"  # Solid + dashed for passing zones
    TURN_ARROW_LEFT = "turn_left"
    TURN_ARROW_RIGHT = "turn_right"
    TURN_ARROW_STRAIGHT = "turn_straight"
    TURN_ARROW_COMBO = "turn_combo"
    EXIT_ARROW = "exit_arrow"
    MERGE_ARROW = "merge_arrow"
    CROSSWALK = "crosswalk"
    STOP_LINE = "stop_line"
    YIELD_LINE = "yield_line"
    SPEED_MARKING = "speed"
    EXIT_NUMBER = "exit_number"


class MarkingColor(Enum):
    """Road marking colors."""
    WHITE = "white"
    YELLOW = "yellow"
    BLUE = "blue"  # Handicap/parking
    RED = "red"    # Fire lane, no parking


@dataclass
class MarkingConfig:
    """Configuration for lane marking generation."""
    # Standard US marking dimensions (in meters)
    dash_length: float = 3.0       # Standard: 10 feet
    dash_gap: float = 9.0          # Standard: 30 feet
    line_width: float = 0.15       # Standard: 6 inches (0.15m)
    edge_line_width: float = 0.20  # Edge lines are wider

    # Double line settings
    double_line_spacing: float = 0.10  # Gap between double lines

    # Paint appearance
    paint_thickness: float = 0.003  # 3mm raised paint
    paint_roughness: float = 0.4
    paint_metallic: float = 0.0

    # Wear and fade
    wear_amount: float = 0.0       # 0-1, how worn the paint is
    edge_chipping: float = 0.1     # Paint edge chipping

    # Material
    emission_strength: float = 0.0  # Reflective paint glow


@dataclass
class MarkingSegment:
    """A single marking segment to be generated."""
    marking_type: MarkingType
    start: Tuple[float, float, float]
    end: Tuple[float, float, float]
    color: MarkingColor = MarkingColor.WHITE
    width: Optional[float] = None  # Override default width
    lanes: int = 2  # Number of lanes (affects some marking types)


# Standard US highway marking configurations
HIGHWAY_MARKING_CONFIG = MarkingConfig(
    dash_length=3.0,
    dash_gap=9.0,
    line_width=0.15,
    edge_line_width=0.20,
)

# Residential road markings
RESIDENTIAL_MARKING_CONFIG = MarkingConfig(
    dash_length=2.5,
    dash_gap=7.5,
    line_width=0.12,
    edge_line_width=0.15,
)


class LaneMarkingGenerator:
    """
    Generates lane marking geometry for roads.

    Creates paint geometry as thin mesh objects that sit slightly
    above the road surface for realistic shading.
    """

    def __init__(self, config: Optional[MarkingConfig] = None):
        """Initialize the lane marking generator."""
        self.config = config or MarkingConfig()
        self._material_cache: Dict[str, Any] = {}

    def generate_dashed_line(
        self,
        start: Tuple[float, float, float],
        end: Tuple[float, float, float],
        color: MarkingColor = MarkingColor.WHITE,
        width: Optional[float] = None,
        name: str = "DashedLine",
        collection: Optional[Collection] = None,
    ) -> List[Object]:
        """
        Generate a dashed line between two points.

        Args:
            start: Start coordinate (x, y, z)
            end: End coordinate (x, y, z)
            color: Marking color
            width: Override line width
            name: Base name for created objects
            collection: Collection to add objects to

        Returns:
            List of created mesh objects
        """
        if not BLENDER_AVAILABLE:
            return []

        objects = []
        width = width or self.config.line_width

        start_v = Vector(start)
        end_v = Vector(end)
        direction = (end_v - start_v).normalized()
        total_length = (end_v - start_v).length

        # Calculate perpendicular for width
        perpendicular = Vector((-direction.y, direction.x, 0))

        # Generate dashes
        cycle_length = self.config.dash_length + self.config.dash_gap
        current_pos = 0.0
        dash_index = 0

        while current_pos < total_length:
            dash_start = current_pos
            dash_end = min(current_pos + self.config.dash_length, total_length)

            if dash_end - dash_start < 0.1:  # Skip tiny dashes
                break

            # Create dash mesh
            obj = self._create_line_segment(
                start=start_v + direction * dash_start,
                end=start_v + direction * dash_end,
                width=width,
                perpendicular=perpendicular,
                name=f"{name}_{dash_index}",
                color=color,
            )

            if obj:
                objects.append(obj)
                if collection:
                    collection.objects.link(obj)

            current_pos += cycle_length
            dash_index += 1

        return objects

    def generate_solid_line(
        self,
        start: Tuple[float, float, float],
        end: Tuple[float, float, float],
        color: MarkingColor = MarkingColor.WHITE,
        width: Optional[float] = None,
        name: str = "SolidLine",
        collection: Optional[Collection] = None,
    ) -> Optional[Object]:
        """
        Generate a solid line between two points.

        Args:
            start: Start coordinate
            end: End coordinate
            color: Marking color
            width: Override line width
            name: Object name
            collection: Collection to add to

        Returns:
            Created mesh object
        """
        if not BLENDER_AVAILABLE:
            return None

        width = width or self.config.line_width

        start_v = Vector(start)
        end_v = Vector(end)
        direction = (end_v - start_v).normalized()
        perpendicular = Vector((-direction.y, direction.x, 0))

        obj = self._create_line_segment(
            start=start_v,
            end=end_v,
            width=width,
            perpendicular=perpendicular,
            name=name,
            color=color,
        )

        if obj and collection:
            collection.objects.link(obj)

        return obj

    def generate_double_line(
        self,
        start: Tuple[float, float, float],
        end: Tuple[float, float, float],
        left_type: MarkingType = MarkingType.SOLID_LINE,
        right_type: MarkingType = MarkingType.SOLID_LINE,
        color: MarkingColor = MarkingColor.YELLOW,
        name: str = "DoubleLine",
        collection: Optional[Collection] = None,
    ) -> List[Object]:
        """
        Generate a double line (two parallel lines).

        Common configurations:
        - Double solid: No passing either direction
        - Double dashed: Passing allowed both directions
        - Solid + dashed: Passing allowed from dashed side

        Args:
            start: Start coordinate
            end: End coordinate
            left_type: Type of left line
            right_type: Type of right line
            color: Marking color (typically yellow for center)
            name: Base name
            collection: Collection to add to

        Returns:
            List of created objects
        """
        objects = []

        start_v = Vector(start)
        end_v = Vector(end)
        direction = (end_v - start_v).normalized()
        perpendicular = Vector((-direction.y, direction.x, 0))

        # Offset for each line
        spacing = self.config.double_line_spacing + self.config.line_width

        # Left line
        left_offset = perpendicular * (spacing / 2)
        left_start = start_v + left_offset
        left_end = end_v + left_offset

        if left_type == MarkingType.SOLID_LINE:
            left_obj = self.generate_solid_line(
                tuple(left_start), tuple(left_end),
                color=color,
                name=f"{name}_Left",
                collection=collection,
            )
            if left_obj:
                objects.append(left_obj)
        else:  # Dashed
            left_objs = self.generate_dashed_line(
                tuple(left_start), tuple(left_end),
                color=color,
                name=f"{name}_Left",
                collection=collection,
            )
            objects.extend(left_objs)

        # Right line
        right_offset = -perpendicular * (spacing / 2)
        right_start = start_v + right_offset
        right_end = end_v + right_offset

        if right_type == MarkingType.SOLID_LINE:
            right_obj = self.generate_solid_line(
                tuple(right_start), tuple(right_end),
                color=color,
                name=f"{name}_Right",
                collection=collection,
            )
            if right_obj:
                objects.append(right_obj)
        else:  # Dashed
            right_objs = self.generate_dashed_line(
                tuple(right_start), tuple(right_end),
                color=color,
                name=f"{name}_Right",
                collection=collection,
            )
            objects.extend(right_objs)

        return objects

    def generate_edge_lines(
        self,
        road_points: List[Tuple[float, float, float]],
        road_width: float,
        is_left: bool = True,
        is_right: bool = True,
        collection: Optional[Collection] = None,
    ) -> List[Object]:
        """
        Generate edge lines along a road path.

        Args:
            road_points: List of points defining road center
            road_width: Total road width
            is_left: Generate left edge line
            is_right: Generate right edge line
            collection: Collection to add to

        Returns:
            List of created objects
        """
        if not BLENDER_AVAILABLE or len(road_points) < 2:
            return []

        objects = []

        # Calculate edge offsets
        edge_offset = (road_width / 2) - self.config.edge_line_width

        for generate_right, offset_sign in [(False, 1), (True, -1)]:
            if generate_right and not is_right:
                continue
            if not generate_right and not is_left:
                continue

            edge_points = []

            for i, point in enumerate(road_points):
                point_v = Vector(point)

                # Calculate direction
                if i == 0:
                    direction = (Vector(road_points[1]) - point_v).normalized()
                elif i == len(road_points) - 1:
                    direction = (point_v - Vector(road_points[-2])).normalized()
                else:
                    direction = (Vector(road_points[i + 1]) - Vector(road_points[i - 1])).normalized()

                perpendicular = Vector((-direction.y, direction.x, 0))
                edge_point = point_v + perpendicular * edge_offset * offset_sign
                edge_points.append(edge_point)

            # Generate solid edge line
            for i in range(len(edge_points) - 1):
                obj = self.generate_solid_line(
                    tuple(edge_points[i]),
                    tuple(edge_points[i + 1]),
                    color=MarkingColor.WHITE,
                    width=self.config.edge_line_width,
                    name=f"EdgeLine_{'R' if generate_right else 'L'}_{i}",
                    collection=collection,
                )
                if obj:
                    objects.append(obj)

        return objects

    def generate_center_line(
        self,
        road_points: List[Tuple[float, float, float]],
        lanes_per_direction: int = 2,
        is_divided: bool = False,
        collection: Optional[Collection] = None,
    ) -> List[Object]:
        """
        Generate center line markings for a road.

        Args:
            road_points: List of points defining road center
            lanes_per_direction: Number of lanes in each direction
            is_divided: Whether road has a physical divider
            collection: Collection to add to

        Returns:
            List of created objects
        """
        if not BLENDER_AVAILABLE or len(road_points) < 2:
            return []

        objects = []

        if is_divided:
            # Divided highway - no center line needed
            return objects

        # Generate center line based on lanes
        if lanes_per_direction == 1:
            # Two-lane road: dashed yellow center
            for i in range(len(road_points) - 1):
                objs = self.generate_dashed_line(
                    road_points[i],
                    road_points[i + 1],
                    color=MarkingColor.YELLOW,
                    name=f"CenterLine_{i}",
                    collection=collection,
                )
                objects.extend(objs)
        else:
            # Multi-lane: double yellow line (solid + solid or solid + dashed)
            for i in range(len(road_points) - 1):
                objs = self.generate_double_line(
                    road_points[i],
                    road_points[i + 1],
                    left_type=MarkingType.SOLID_LINE,
                    right_type=MarkingType.SOLID_LINE,
                    color=MarkingColor.YELLOW,
                    name=f"CenterLine_{i}",
                    collection=collection,
                )
                objects.extend(objs)

        return objects

    def generate_lane_lines(
        self,
        road_points: List[Tuple[float, float, float]],
        road_width: float,
        lane_count: int,
        collection: Optional[Collection] = None,
    ) -> List[Object]:
        """
        Generate lane separator lines for a multi-lane road.

        Args:
            road_points: Road center line points
            road_width: Total road width
            lane_count: Number of lanes
            collection: Collection to add to

        Returns:
            List of created objects
        """
        if not BLENDER_AVAILABLE or lane_count < 2:
            return []

        objects = []
        lane_width = road_width / lane_count

        # Generate lane separators (skip edges and center if center line exists)
        for lane_idx in range(1, lane_count):
            # Skip center line position (will be handled separately)
            if lane_idx == lane_count // 2:
                continue

            offset = -road_width / 2 + lane_idx * lane_width

            lane_points = []
            for i, point in enumerate(road_points):
                point_v = Vector(point)

                # Calculate perpendicular
                if i == 0:
                    direction = (Vector(road_points[1]) - point_v).normalized()
                elif i == len(road_points) - 1:
                    direction = (point_v - Vector(road_points[-2])).normalized()
                else:
                    direction = (Vector(road_points[i + 1]) - Vector(road_points[i - 1])).normalized()

                perpendicular = Vector((-direction.y, direction.x, 0))
                lane_point = point_v + perpendicular * offset
                lane_points.append(lane_point)

            # Generate dashed white lane line
            for i in range(len(lane_points) - 1):
                objs = self.generate_dashed_line(
                    tuple(lane_points[i]),
                    tuple(lane_points[i + 1]),
                    color=MarkingColor.WHITE,
                    name=f"LaneLine_{lane_idx}_{i}",
                    collection=collection,
                )
                objects.extend(objs)

        return objects

    def _create_line_segment(
        self,
        start: Vector,
        end: Vector,
        width: float,
        perpendicular: Vector,
        name: str,
        color: MarkingColor,
    ) -> Optional[Object]:
        """Create a single line segment mesh."""
        if not BLENDER_AVAILABLE:
            return None

        # Create mesh
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        # Create vertices for thin rectangle
        half_width = width / 2
        z_offset = self.config.paint_thickness  # Slightly above surface

        verts = [
            start + perpendicular * half_width + Vector((0, 0, z_offset)),
            start - perpendicular * half_width + Vector((0, 0, z_offset)),
            end - perpendicular * half_width + Vector((0, 0, z_offset)),
            end + perpendicular * half_width + Vector((0, 0, z_offset)),
        ]

        # Create face
        faces = [[0, 1, 2, 3]]

        mesh.from_pydata([v.to_tuple() for v in verts], [], faces)
        mesh.update()

        # Apply material
        mat = self._get_marking_material(color)
        if mat:
            obj.data.materials.append(mat)

        return obj

    def _get_marking_material(self, color: MarkingColor) -> Optional[Any]:
        """Get or create marking material."""
        if not BLENDER_AVAILABLE:
            return None

        cache_key = f"marking_{color.value}"

        if cache_key in self._material_cache:
            return self._material_cache[cache_key]

        # Create material
        mat_name = f"RoadMarking_{color.value}"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        # BSDF
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (0, 0)

        # Set color
        color_values = {
            MarkingColor.WHITE: (0.95, 0.95, 0.95, 1.0),
            MarkingColor.YELLOW: (0.9, 0.8, 0.1, 1.0),
            MarkingColor.BLUE: (0.1, 0.3, 0.9, 1.0),
            MarkingColor.RED: (0.9, 0.1, 0.1, 1.0),
        }

        bsdf.inputs["Base Color"].default_value = color_values.get(color, color_values[MarkingColor.WHITE])
        bsdf.inputs["Roughness"].default_value = self.config.paint_roughness
        bsdf.inputs["Metallic"].default_value = self.config.paint_metallic

        # Add slight emission for reflective paint
        if self.config.emission_strength > 0:
            bsdf.inputs["Emission Color"].default_value = color_values.get(color, color_values[MarkingColor.WHITE])
            bsdf.inputs["Emission Strength"].default_value = self.config.emission_strength

        # Output
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (200, 0)

        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        self._material_cache[cache_key] = mat
        return mat


def generate_highway_markings(
    road_points: List[Tuple[float, float, float]],
    road_width: float,
    lanes_per_direction: int = 2,
    is_divided: bool = True,
    config: Optional[MarkingConfig] = None,
    collection: Optional[Collection] = None,
) -> Dict[str, List[Object]]:
    """
    Generate complete highway road markings.

    Args:
        road_points: Center line points
        road_width: Total road width
        lanes_per_direction: Lanes in each direction
        is_divided: Has physical median
        config: Marking configuration
        collection: Collection to add objects to

    Returns:
        Dictionary of created objects by type
    """
    generator = LaneMarkingGenerator(config or HIGHWAY_MARKING_CONFIG)

    results = {
        "edge_lines": [],
        "center_line": [],
        "lane_lines": [],
    }

    # Edge lines
    results["edge_lines"] = generator.generate_edge_lines(
        road_points, road_width,
        is_left=True, is_right=True,
        collection=collection,
    )

    # Center line (if not divided)
    if not is_divided:
        results["center_line"] = generator.generate_center_line(
            road_points,
            lanes_per_direction=lanes_per_direction,
            is_divided=is_divided,
            collection=collection,
        )

    # Lane lines
    total_lanes = lanes_per_direction * (2 if not is_divided else 1)
    results["lane_lines"] = generator.generate_lane_lines(
        road_points, road_width, total_lanes,
        collection=collection,
    )

    return results


__all__ = [
    "MarkingType",
    "MarkingColor",
    "MarkingConfig",
    "MarkingSegment",
    "LaneMarkingGenerator",
    "HIGHWAY_MARKING_CONFIG",
    "RESIDENTIAL_MARKING_CONFIG",
    "generate_highway_markings",
]
