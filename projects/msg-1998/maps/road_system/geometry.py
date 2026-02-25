"""
MSG-1998 Road Geometry Builders

Generates geometry for:
- Pavement (road surface)
- Curbs (raised edge between road and sidewalk)
- Sidewalks (pedestrian walking surface)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
import math


@dataclass
class GeometryResult:
    """Result of geometry generation."""
    vertices: List[Tuple[float, float, float]] = field(default_factory=list)
    faces: List[Tuple[int, ...]] = field(default_factory=list)
    uvs: List[Tuple[float, float]] = field(default_factory=list)
    material_index: int = 0
    object_name: str = ""


class PavementBuilder:
    """
    Builds road pavement geometry from road centerlines.

    Creates the main road surface with proper width and cross-fall.
    """

    def __init__(
        self,
        default_material: str = "asphalt_nyc_1998",
        cross_fall: float = 0.02,  # 2% slope for drainage
        thickness: float = 0.05,   # 5cm asphalt thickness
    ):
        """
        Initialize pavement builder.

        Args:
            default_material: Material name for pavement
            cross_fall: Cross slope for drainage (ratio)
            thickness: Asphalt thickness in meters
        """
        self.default_material = default_material
        self.cross_fall = cross_fall
        self.thickness = thickness

    def build(
        self,
        vertices: List[Tuple[float, float, float]],
        width: float,
        road_name: str = "road",
    ) -> GeometryResult:
        """
        Build pavement geometry from road centerline vertices.

        Args:
            vertices: Centerline vertices of the road
            width: Road width in meters
            road_name: Name for the resulting object

        Returns:
            GeometryResult with pavement mesh data
        """
        if len(vertices) < 2:
            return GeometryResult(object_name=f"{road_name}_pavement")

        result = GeometryResult(object_name=f"{road_name}_pavement")
        half_width = width / 2

        # Generate cross-section at each vertex
        for i, (x, y, z) in enumerate(vertices):
            # Calculate direction at this point
            if i == 0:
                # First point: use direction to next
                dx = vertices[1][0] - x
                dy = vertices[1][1] - y
            elif i == len(vertices) - 1:
                # Last point: use direction from previous
                dx = x - vertices[-2][0]
                dy = y - vertices[-2][1]
            else:
                # Middle point: average direction
                dx1 = vertices[i + 1][0] - x
                dy1 = vertices[i + 1][1] - y
                dx2 = x - vertices[i - 1][0]
                dy2 = y - vertices[i - 1][1]
                dx = (dx1 + dx2) / 2
                dy = (dy1 + dy2) / 2

            # Normalize direction
            length = math.sqrt(dx * dx + dy * dy)
            if length < 0.001:
                dx, dy = 1.0, 0.0
            else:
                dx /= length
                dy /= length

            # Perpendicular direction
            px, py = -dy, dx

            # Create left and right edge vertices
            # Apply cross-fall (edges slightly lower than center)
            edge_z = z - self.cross_fall * half_width

            # Left edge
            result.vertices.append((
                x - px * half_width,
                y - py * half_width,
                edge_z,
            ))

            # Right edge
            result.vertices.append((
                x + px * half_width,
                y + py * half_width,
                edge_z,
            ))

        # Generate faces connecting the cross-sections
        n_cross_sections = len(vertices)
        for i in range(n_cross_sections - 1):
            # Quad between cross-sections
            # Left edge: i*2, Right edge: i*2+1
            v0 = i * 2       # Current left
            v1 = i * 2 + 1   # Current right
            v2 = (i + 1) * 2 + 1  # Next right
            v3 = (i + 1) * 2      # Next left

            result.faces.append((v0, v1, v2, v3))

        # Generate UVs (tile along road)
        result.uvs = self._generate_uvs(vertices, width)

        return result

    def _generate_uvs(
        self,
        vertices: List[Tuple[float, float, float]],
        width: float,
    ) -> List[Tuple[float, float]]:
        """Generate UV coordinates for pavement."""
        uvs = []
        accumulated_length = 0.0

        for i in range(len(vertices)):
            if i > 0:
                # Calculate segment length
                dx = vertices[i][0] - vertices[i - 1][0]
                dy = vertices[i][1] - vertices[i - 1][1]
                accumulated_length += math.sqrt(dx * dx + dy * dy)

            # U coordinate along road (tile every 10 meters)
            u = (accumulated_length / 10.0) % 1.0

            # Left edge (V=0), Right edge (V=1)
            uvs.append((u, 0.0))  # Left
            uvs.append((u, 1.0))  # Right

        return uvs


class CurbBuilder:
    """
    Builds curb geometry along road edges.

    Creates the raised edge between pavement and sidewalk
    with proper profile and height.
    """

    def __init__(
        self,
        height: float = 0.15,      # 15cm standard NYC curb
        width_top: float = 0.15,   # 15cm top width
        width_bottom: float = 0.20, # 20cm bottom width (sloped)
        material: str = "concrete_curb",
    ):
        """
        Initialize curb builder.

        Args:
            height: Curb height in meters
            width_top: Top surface width
            width_bottom: Bottom width (includes slope)
            material: Material name for curbs
        """
        self.height = height
        self.width_top = width_top
        self.width_bottom = width_bottom
        self.material = material

    def build(
        self,
        road_vertices: List[Tuple[float, float, float]],
        road_width: float,
        side: str = "both",  # "left", "right", or "both"
        road_name: str = "road",
    ) -> GeometryResult:
        """
        Build curb geometry along road edges.

        Args:
            road_vertices: Centerline vertices of the road
            road_width: Road width in meters
            side: Which side(s) to build curbs on
            road_name: Name for the resulting object

        Returns:
            GeometryResult with curb mesh data
        """
        if len(road_vertices) < 2:
            return GeometryResult(object_name=f"{road_name}_curb")

        result = GeometryResult(object_name=f"{road_name}_curb")
        half_width = road_width / 2

        sides_to_build = []
        if side in ("left", "both"):
            sides_to_build.append(("left", -1))
        if side in ("right", "both"):
            sides_to_build.append(("right", 1))

        vertex_offset = 0

        for side_name, side_dir in sides_to_build:
            # Generate curb profile at each vertex
            for i, (x, y, z) in enumerate(road_vertices):
                # Calculate direction and perpendicular
                if i == 0:
                    dx = road_vertices[1][0] - x
                    dy = road_vertices[1][1] - y
                elif i == len(road_vertices) - 1:
                    dx = x - road_vertices[-2][0]
                    dy = y - road_vertices[-2][1]
                else:
                    dx1 = road_vertices[i + 1][0] - x
                    dy1 = road_vertices[i + 1][1] - y
                    dx2 = x - road_vertices[i - 1][0]
                    dy2 = y - road_vertices[i - 1][1]
                    dx = (dx1 + dx2) / 2
                    dy = (dy1 + dy2) / 2

                length = math.sqrt(dx * dx + dy * dy)
                if length < 0.001:
                    dx, dy = 1.0, 0.0
                else:
                    dx /= length
                    dy /= length

                px, py = -dy, dx

                # Road edge position
                edge_x = x + side_dir * px * half_width
                edge_y = y + side_dir * py * half_width

                # Curb profile vertices (bottom to top, outside to inside)
                # 1. Bottom outside (at road level)
                result.vertices.append((
                    edge_x + side_dir * px * self.width_bottom,
                    edge_y + side_dir * py * self.width_bottom,
                    z,
                ))

                # 2. Top outside
                result.vertices.append((
                    edge_x + side_dir * px * self.width_top,
                    edge_y + side_dir * py * self.width_top,
                    z + self.height,
                ))

                # 3. Top inside (at road edge)
                result.vertices.append((
                    edge_x,
                    edge_y,
                    z + self.height,
                ))

                # 4. Bottom inside (at road edge, road level)
                result.vertices.append((
                    edge_x,
                    edge_y,
                    z,
                ))

            # Generate faces
            n_profiles = len(road_vertices)
            for i in range(n_profiles - 1):
                # Each profile has 4 vertices
                base = vertex_offset + i * 4
                next_base = vertex_offset + (i + 1) * 4

                # Front face (vertical)
                result.faces.append((base, next_base, next_base + 1, base + 1))

                # Top face
                result.faces.append((base + 1, next_base + 1, next_base + 2, base + 2))

                # Back face (toward road)
                result.faces.append((base + 2, next_base + 2, next_base + 3, base + 3))

            vertex_offset += n_profiles * 4

        return result


class SidewalkBuilder:
    """
    Builds sidewalk geometry along road edges.

    Creates pedestrian walking surfaces with proper width
    and connection to curbs.
    """

    def __init__(
        self,
        default_width: float = 2.0,
        material: str = "concrete_sidewalk",
        thickness: float = 0.10,
        pattern_size: float = 1.5,  # Size of concrete slabs
    ):
        """
        Initialize sidewalk builder.

        Args:
            default_width: Default sidewalk width in meters
            material: Material name for sidewalks
            thickness: Sidewalk thickness in meters
            pattern_size: Size of concrete slab pattern in meters
        """
        self.default_width = default_width
        self.material = material
        self.thickness = thickness
        self.pattern_size = pattern_size

    def build(
        self,
        road_vertices: List[Tuple[float, float, float]],
        road_width: float,
        sidewalk_width: Optional[float] = None,
        curb_height: float = 0.15,
        side: str = "both",
        road_name: str = "road",
    ) -> GeometryResult:
        """
        Build sidewalk geometry along road edges.

        Args:
            road_vertices: Centerline vertices of the road
            road_width: Road width in meters
            sidewalk_width: Sidewalk width (uses default if None)
            curb_height: Height of adjacent curb
            side: Which side(s) to build sidewalks on
            road_name: Name for the resulting object

        Returns:
            GeometryResult with sidewalk mesh data
        """
        if len(road_vertices) < 2:
            return GeometryResult(object_name=f"{road_name}_sidewalk")

        width = sidewalk_width or self.default_width
        result = GeometryResult(object_name=f"{road_name}_sidewalk")
        half_road = road_width / 2

        sides_to_build = []
        if side in ("left", "both"):
            sides_to_build.append(("left", -1))
        if side in ("right", "both"):
            sides_to_build.append(("right", 1))

        for side_name, side_dir in sides_to_build:
            # Generate sidewalk vertices at each point
            for i, (x, y, z) in enumerate(road_vertices):
                # Calculate direction and perpendicular
                if i == 0:
                    dx = road_vertices[1][0] - x
                    dy = road_vertices[1][1] - y
                elif i == len(road_vertices) - 1:
                    dx = x - road_vertices[-2][0]
                    dy = y - road_vertices[-2][1]
                else:
                    dx1 = road_vertices[i + 1][0] - x
                    dy1 = road_vertices[i + 1][1] - y
                    dx2 = x - road_vertices[i - 1][0]
                    dy2 = y - road_vertices[i - 1][1]
                    dx = (dx1 + dx2) / 2
                    dy = (dy1 + dy2) / 2

                length = math.sqrt(dx * dx + dy * dy)
                if length < 0.001:
                    dx, dy = 1.0, 0.0
                else:
                    dx /= length
                    dy /= length

                px, py = -dy, dx

                # Sidewalk inner edge (at curb)
                inner_x = x + side_dir * px * half_road
                inner_y = y + side_dir * py * half_road

                # Sidewalk outer edge
                outer_x = inner_x + side_dir * px * width
                outer_y = inner_y + side_dir * py * width

                # Sidewalk surface is at curb height
                sidewalk_z = z + curb_height

                # Inner vertices (2 per cross-section for thickness)
                result.vertices.append((inner_x, inner_y, sidewalk_z))
                result.vertices.append((inner_x, inner_y, sidewalk_z - self.thickness))

                # Outer vertices
                result.vertices.append((outer_x, outer_y, sidewalk_z))
                result.vertices.append((outer_x, outer_y, sidewalk_z - self.thickness))

            # Generate faces
            n_profiles = len(road_vertices)
            base_idx = 0 if side_name == "left" else len(road_vertices) * 4

            for i in range(n_profiles - 1):
                base = base_idx + i * 4
                next_base = base_idx + (i + 1) * 4

                # Top surface
                result.faces.append((base, next_base, next_base + 2, base + 2))

                # Front edge
                result.faces.append((base + 2, next_base + 2, next_base + 3, base + 3))

                # Back edge (toward curb)
                result.faces.append((base + 1, next_base + 1, next_base, base))

                # Bottom
                result.faces.append((base + 3, next_base + 3, next_base + 1, base + 1))

        return result


class RoadGeometryBuilder:
    """
    High-level builder that coordinates pavement, curb, and sidewalk generation.
    """

    def __init__(
        self,
        pavement_builder: Optional[PavementBuilder] = None,
        curb_builder: Optional[CurbBuilder] = None,
        sidewalk_builder: Optional[SidewalkBuilder] = None,
    ):
        """
        Initialize with optional custom builders.

        Args:
            pavement_builder: Custom pavement builder
            curb_builder: Custom curb builder
            sidewalk_builder: Custom sidewalk builder
        """
        self.pavement = pavement_builder or PavementBuilder()
        self.curb = curb_builder or CurbBuilder()
        self.sidewalk = sidewalk_builder or SidewalkBuilder()

    def build_all(
        self,
        road_vertices: List[Tuple[float, float, float]],
        road_width: float,
        sidewalk_width: Optional[float] = None,
        has_curb: bool = True,
        has_sidewalk: bool = True,
        road_name: str = "road",
    ) -> Dict[str, GeometryResult]:
        """
        Build all road geometry components.

        Args:
            road_vertices: Centerline vertices
            road_width: Road width in meters
            sidewalk_width: Sidewalk width (None for default)
            has_curb: Whether to build curbs
            has_sidewalk: Whether to build sidewalks
            road_name: Base name for objects

        Returns:
            Dict with "pavement", "curb", "sidewalk" GeometryResults
        """
        results = {}

        # Build pavement
        results["pavement"] = self.pavement.build(
            vertices=road_vertices,
            width=road_width,
            road_name=road_name,
        )

        # Build curbs
        if has_curb:
            results["curb"] = self.curb.build(
                road_vertices=road_vertices,
                road_width=road_width,
                side="both",
                road_name=road_name,
            )
        else:
            results["curb"] = GeometryResult(object_name=f"{road_name}_curb")

        # Build sidewalks
        if has_sidewalk:
            results["sidewalk"] = self.sidewalk.build(
                road_vertices=road_vertices,
                road_width=road_width,
                sidewalk_width=sidewalk_width,
                curb_height=self.curb.height if has_curb else 0.0,
                side="both",
                road_name=road_name,
            )
        else:
            results["sidewalk"] = GeometryResult(object_name=f"{road_name}_sidewalk")

        return results


__all__ = [
    "GeometryResult",
    "PavementBuilder",
    "CurbBuilder",
    "SidewalkBuilder",
    "RoadGeometryBuilder",
]
