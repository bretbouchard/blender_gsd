"""
MSG-1998 Street Furniture Distribution

Distributes street furniture along roads:
- Manhole covers
- Fire hydrants
- Street signs
- Traffic signals
- Trash cans
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Set
from enum import Enum
import math
import random


class FurnitureType(Enum):
    """Types of street furniture."""
    MANHOLE_SEWER = "manhole_sewer"
    MANHOLE_WATER = "manhole_water"
    MANHOLE_GAS = "manhole_gas"
    MANHOLE_ELECTRIC = "manhole_electric"
    MANHOLE_CONED = "manhole_coned"  # NYC iconic conEdison covers
    FIRE_HYDRANT = "fire_hydrant"
    STREET_SIGN = "street_sign"
    STOP_SIGN = "stop_sign"
    TRAFFIC_SIGNAL = "traffic_signal"
    TRASH_CAN = "trash_can"
    PARKING_METER = "parking_meter"
    NEWSPAPER_BOX = "newspaper_box"


@dataclass
class StreetFurniture:
    """Specification for a street furniture item."""
    furniture_type: FurnitureType
    position: Tuple[float, float, float]
    rotation: float  # Radians
    scale: float = 1.0
    lod_level: int = 0
    road_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FurnitureDistribution:
    """Distribution configuration for a furniture type."""
    furniture_type: FurnitureType
    spacing_min: float  # Minimum spacing in meters
    spacing_max: float  # Maximum spacing in meters
    offset_from_edge: float  # Distance from road edge
    placement_side: str  # "left", "right", "center", "both"
    require_intersection: bool = False  # Only place at intersections
    avoid_intersections: bool = True  # Avoid placing near intersections
    intersection_clearance: float = 10.0  # Meters to keep clear of intersections
    random_offset: float = 0.0  # Random position variance


# Default distribution configurations
FURNITURE_DISTRIBUTIONS: Dict[FurnitureType, FurnitureDistribution] = {
    FurnitureType.MANHOLE_SEWER: FurnitureDistribution(
        furniture_type=FurnitureType.MANHOLE_SEWER,
        spacing_min=30.0,
        spacing_max=50.0,
        offset_from_edge=0.0,  # Center of lane
        placement_side="center",
        require_intersection=False,
        avoid_intersections=True,
        intersection_clearance=5.0,
        random_offset=0.5,
    ),
    FurnitureType.MANHOLE_WATER: FurnitureDistribution(
        furniture_type=FurnitureType.MANHOLE_WATER,
        spacing_min=40.0,
        spacing_max=60.0,
        offset_from_edge=0.0,
        placement_side="center",
        require_intersection=False,
        avoid_intersections=True,
        intersection_clearance=5.0,
        random_offset=0.5,
    ),
    FurnitureType.MANHOLE_CONED: FurnitureDistribution(
        furniture_type=FurnitureType.MANHOLE_CONED,
        spacing_min=35.0,
        spacing_max=55.0,
        offset_from_edge=0.0,
        placement_side="center",
        require_intersection=False,
        avoid_intersections=True,
        intersection_clearance=5.0,
        random_offset=0.5,
    ),
    FurnitureType.FIRE_HYDRANT: FurnitureDistribution(
        furniture_type=FurnitureType.FIRE_HYDRANT,
        spacing_min=100.0,  # ~300ft standard
        spacing_max=150.0,
        offset_from_edge=0.5,  # Half meter from curb
        placement_side="right",
        require_intersection=False,
        avoid_intersections=False,
        intersection_clearance=3.0,
        random_offset=0.3,
    ),
    FurnitureType.STREET_SIGN: FurnitureDistribution(
        furniture_type=FurnitureType.STREET_SIGN,
        spacing_min=0.0,
        spacing_max=0.0,
        offset_from_edge=0.3,
        placement_side="both",
        require_intersection=True,  # Only at intersections
        avoid_intersections=False,
        intersection_clearance=0.0,
        random_offset=0.0,
    ),
    FurnitureType.STOP_SIGN: FurnitureDistribution(
        furniture_type=FurnitureType.STOP_SIGN,
        spacing_min=0.0,
        spacing_max=0.0,
        offset_from_edge=0.3,
        placement_side="right",
        require_intersection=True,
        avoid_intersections=False,
        intersection_clearance=0.0,
        random_offset=0.0,
    ),
    FurnitureType.TRAFFIC_SIGNAL: FurnitureDistribution(
        furniture_type=FurnitureType.TRAFFIC_SIGNAL,
        spacing_min=0.0,
        spacing_max=0.0,
        offset_from_edge=0.0,
        placement_side="both",
        require_intersection=True,
        avoid_intersections=False,
        intersection_clearance=0.0,
        random_offset=0.0,
    ),
    FurnitureType.TRASH_CAN: FurnitureDistribution(
        furniture_type=FurnitureType.TRASH_CAN,
        spacing_min=50.0,
        spacing_max=100.0,
        offset_from_edge=0.3,
        placement_side="right",
        require_intersection=False,
        avoid_intersections=True,
        intersection_clearance=15.0,
        random_offset=0.2,
    ),
    FurnitureType.PARKING_METER: FurnitureDistribution(
        furniture_type=FurnitureType.PARKING_METER,
        spacing_min=5.0,
        spacing_max=7.0,
        offset_from_edge=0.2,
        placement_side="right",
        require_intersection=False,
        avoid_intersections=True,
        intersection_clearance=10.0,
        random_offset=0.1,
    ),
}


class ManholePlacer:
    """
    Specialized placer for manhole covers.

    Manholes are typically in the center of lanes and follow
    specific patterns based on NYC infrastructure.
    """

    # Manhole types and their relative frequencies in NYC
    MANHOLE_WEIGHTS = {
        FurnitureType.MANHOLE_SEWER: 0.35,
        FurnitureType.MANHOLE_WATER: 0.25,
        FurnitureType.MANHOLE_CONED: 0.25,
        FurnitureType.MANHOLE_GAS: 0.10,
        FurnitureType.MANHOLE_ELECTRIC: 0.05,
    }

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize manhole placer.

        Args:
            seed: Random seed for reproducibility
        """
        self.rng = random.Random(seed)

    def place(
        self,
        road_vertices: List[Tuple[float, float, float]],
        road_width: float,
        road_name: str,
        intersection_positions: List[Tuple[float, float]],
        spacing: float = 40.0,
    ) -> List[StreetFurniture]:
        """
        Place manholes along a road.

        Args:
            road_vertices: Road centerline vertices
            road_width: Road width in meters
            road_name: Road name
            intersection_positions: Centers of nearby intersections
            spacing: Average spacing between manholes

        Returns:
            List of StreetFurniture items
        """
        if len(road_vertices) < 2:
            return []

        furniture = []
        road_width = road_width or 10.0  # Default if None
        half_width = road_width / 2

        # Calculate road length
        total_length = 0.0
        segments = [(0.0, road_vertices[0])]
        for i in range(1, len(road_vertices)):
            dx = road_vertices[i][0] - road_vertices[i - 1][0]
            dy = road_vertices[i][1] - road_vertices[i - 1][1]
            total_length += math.sqrt(dx * dx + dy * dy)
            segments.append((total_length, road_vertices[i]))

        # Place manholes at intervals
        pos = spacing / 2  # Start offset
        while pos < total_length - spacing / 2:
            # Get position along road
            pos_info = self._get_position_at_length(segments, pos)
            if pos_info is None:
                break

            (px, py, pz), dx, dy = pos_info

            # Check clearance from intersections
            if self._too_close_to_intersection((px, py), intersection_positions, 5.0):
                pos += spacing / 2
                continue

            # Random offset perpendicular to road
            perp_x, perp_y = -dy, dx
            offset = self.rng.uniform(-0.5, 0.5)
            final_x = px + perp_x * offset
            final_y = py + perp_y * offset

            # Select manhole type
            manhole_type = self._select_manhole_type()

            # Calculate rotation (manholes often slightly rotated)
            rotation = self.rng.uniform(-0.1, 0.1)

            furniture.append(StreetFurniture(
                furniture_type=manhole_type,
                position=(final_x, final_y, pz + 0.01),
                rotation=rotation,
                road_id=road_name,
                metadata={"cover_diameter": 0.6},  # 60cm standard
            ))

            # Next position with some randomness
            pos += spacing * self.rng.uniform(0.8, 1.2)

        return furniture

    def _get_position_at_length(
        self,
        segments: List[Tuple[float, Tuple[float, float, float]]],
        target_length: float,
    ) -> Optional[Tuple[Tuple[float, float, float], float, float]]:
        """Get interpolated position at length along road."""
        for i in range(1, len(segments)):
            seg_start_len, seg_start_pos = segments[i - 1]
            seg_end_len, seg_end_pos = segments[i]

            if seg_start_len <= target_length <= seg_end_len:
                seg_length = seg_end_len - seg_start_len
                if seg_length < 0.001:
                    t = 0.0
                else:
                    t = (target_length - seg_start_len) / seg_length

                x = seg_start_pos[0] + t * (seg_end_pos[0] - seg_start_pos[0])
                y = seg_start_pos[1] + t * (seg_end_pos[1] - seg_start_pos[1])
                z = seg_start_pos[2] + t * (seg_end_pos[2] - seg_start_pos[2])

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

    def _too_close_to_intersection(
        self,
        pos: Tuple[float, float],
        intersections: List[Tuple[float, float]],
        clearance: float,
    ) -> bool:
        """Check if position is too close to any intersection."""
        for ix, iy in intersections:
            dist = math.sqrt((pos[0] - ix) ** 2 + (pos[1] - iy) ** 2)
            if dist < clearance:
                return True
        return False

    def _select_manhole_type(self) -> FurnitureType:
        """Randomly select a manhole type based on weights."""
        r = self.rng.random()
        cumulative = 0.0
        for manhole_type, weight in self.MANHOLE_WEIGHTS.items():
            cumulative += weight
            if r < cumulative:
                return manhole_type
        return FurnitureType.MANHOLE_SEWER


class FurnitureDistributor:
    """
    High-level distributor for all street furniture.

    Coordinates placement of various furniture types based on
    road characteristics and intersection positions.
    """

    def __init__(
        self,
        seed: Optional[int] = None,
        lod_distances: Optional[Dict[int, float]] = None,
    ):
        """
        Initialize distributor.

        Args:
            seed: Random seed for reproducibility
            lod_distances: Distance thresholds for LOD levels
        """
        self.seed = seed
        self.rng = random.Random(seed)
        self.manhole_placer = ManholePlacer(seed)

        self.lod_distances = lod_distances or {
            0: 0.0,    # LOD0: Always high detail
            1: 100.0,  # LOD1: Within 100m
            2: 300.0,  # LOD2: Within 300m
            3: 1000.0, # LOD3: Beyond 300m
        }

    def distribute(
        self,
        road_segments: List[Dict[str, Any]],
        intersections: List[Tuple[float, float, float]],
        furniture_types: Optional[Set[FurnitureType]] = None,
        lod_mode: str = "hero",  # "hero" or "city"
    ) -> List[StreetFurniture]:
        """
        Distribute furniture along multiple road segments.

        Args:
            road_segments: List of road segment dicts
            intersections: List of intersection center positions
            furniture_types: Types to distribute (None = all appropriate)
            lod_mode: "hero" for high detail, "city" for optimized

        Returns:
            List of StreetFurniture items
        """
        all_furniture = []
        intersection_2d = [(p[0], p[1]) for p in intersections]

        # Default furniture types based on mode
        if furniture_types is None:
            if lod_mode == "hero":
                furniture_types = {
                    FurnitureType.MANHOLE_SEWER,
                    FurnitureType.MANHOLE_WATER,
                    FurnitureType.MANHOLE_CONED,
                    FurnitureType.FIRE_HYDRANT,
                    FurnitureType.TRASH_CAN,
                    FurnitureType.STREET_SIGN,
                }
            else:
                furniture_types = {
                    FurnitureType.MANHOLE_SEWER,
                    FurnitureType.FIRE_HYDRANT,
                }

        for segment in road_segments:
            road_name = segment.get("name", segment.get("id", "unknown"))
            vertices = segment.get("vertices", [])
            width = segment.get("width", 10.0)

            if len(vertices) < 2:
                continue

            # Distribute manholes
            if any(ft in furniture_types for ft in [
                FurnitureType.MANHOLE_SEWER,
                FurnitureType.MANHOLE_WATER,
                FurnitureType.MANHOLE_CONED,
            ]):
                manholes = self.manhole_placer.place(
                    road_vertices=vertices,
                    road_width=width,
                    road_name=road_name,
                    intersection_positions=intersection_2d,
                )
                all_furniture.extend(manholes)

            # Distribute other furniture types
            for ft in furniture_types:
                if ft in (FurnitureType.MANHOLE_SEWER, FurnitureType.MANHOLE_WATER,
                          FurnitureType.MANHOLE_CONED):
                    continue  # Already handled

                items = self._distribute_type(
                    segment=segment,
                    furniture_type=ft,
                    intersections=intersection_2d,
                )
                all_furniture.extend(items)

        return all_furniture

    def _distribute_type(
        self,
        segment: Dict[str, Any],
        furniture_type: FurnitureType,
        intersections: List[Tuple[float, float]],
    ) -> List[StreetFurniture]:
        """Distribute a specific furniture type along a segment."""
        dist_config = FURNITURE_DISTRIBUTIONS.get(furniture_type)
        if not dist_config:
            return []

        vertices = segment.get("vertices", [])
        width = segment.get("width", 10.0)
        road_name = segment.get("name", segment.get("id", "unknown"))

        if len(vertices) < 2:
            return []

        furniture = []

        if dist_config.require_intersection:
            # Only place at intersections
            for ix, iy in intersections:
                # Check if intersection is on this road
                on_road = self._point_near_road((ix, iy), vertices, width)
                if on_road:
                    item = self._create_furniture_at_intersection(
                        furniture_type, (ix, iy, 0), vertices, dist_config
                    )
                    if item:
                        item.road_id = road_name
                        furniture.append(item)
        else:
            # Distribute along road
            items = self._distribute_along_road(
                vertices=vertices,
                road_width=width,
                furniture_type=furniture_type,
                config=dist_config,
                intersections=intersections,
            )
            for item in items:
                item.road_id = road_name
            furniture.extend(items)

        return furniture

    def _distribute_along_road(
        self,
        vertices: List[Tuple[float, float, float]],
        road_width: float,
        furniture_type: FurnitureType,
        config: FurnitureDistribution,
        intersections: List[Tuple[float, float]],
    ) -> List[StreetFurniture]:
        """Distribute furniture along a road."""
        furniture = []

        # Handle None width
        road_width = road_width or 10.0

        # Calculate road length
        total_length = 0.0
        segments = [(0.0, vertices[0])]
        for i in range(1, len(vertices)):
            dx = vertices[i][0] - vertices[i - 1][0]
            dy = vertices[i][1] - vertices[i - 1][1]
            total_length += math.sqrt(dx * dx + dy * dy)
            segments.append((total_length, vertices[i]))

        if total_length < config.spacing_min:
            return furniture

        # Calculate spacing
        spacing = self.rng.uniform(config.spacing_min, config.spacing_max)
        half_width = road_width / 2

        pos = spacing / 2
        while pos < total_length - spacing / 2:
            pos_info = self._get_position_at_length(segments, pos)
            if pos_info is None:
                break

            (px, py, pz), dx, dy = pos_info

            # Check intersection clearance
            if config.avoid_intersections:
                too_close = False
                for ix, iy in intersections:
                    dist = math.sqrt((px - ix) ** 2 + (py - iy) ** 2)
                    if dist < config.intersection_clearance:
                        too_close = True
                        break
                if too_close:
                    pos += config.intersection_clearance / 2
                    continue

            # Calculate perpendicular offset
            perp_x, perp_y = -dy, dx

            # Determine side
            side_mult = 1.0
            if config.placement_side == "left":
                side_mult = -1.0
            elif config.placement_side == "both":
                side_mult = 1.0 if self.rng.random() > 0.5 else -1.0

            # Apply offset
            offset_x = side_mult * perp_x * (half_width + config.offset_from_edge)
            offset_y = side_mult * perp_y * (half_width + config.offset_from_edge)

            # Random variance
            if config.random_offset > 0:
                offset_x += self.rng.uniform(-config.random_offset, config.random_offset)
                offset_y += self.rng.uniform(-config.random_offset, config.random_offset)

            # Rotation perpendicular to road
            rotation = math.atan2(perp_y, perp_x) * side_mult

            furniture.append(StreetFurniture(
                furniture_type=furniture_type,
                position=(px + offset_x, py + offset_y, pz),
                rotation=rotation,
            ))

            pos += self.rng.uniform(config.spacing_min, config.spacing_max)

        return furniture

    def _get_position_at_length(
        self,
        segments: List[Tuple[float, Tuple[float, float, float]]],
        target_length: float,
    ) -> Optional[Tuple[Tuple[float, float, float], float, float]]:
        """Get interpolated position at length."""
        for i in range(1, len(segments)):
            seg_start_len, seg_start_pos = segments[i - 1]
            seg_end_len, seg_end_pos = segments[i]

            if seg_start_len <= target_length <= seg_end_len:
                seg_length = seg_end_len - seg_start_len
                t = (target_length - seg_start_len) / max(seg_length, 0.001)

                x = seg_start_pos[0] + t * (seg_end_pos[0] - seg_start_pos[0])
                y = seg_start_pos[1] + t * (seg_end_pos[1] - seg_start_pos[1])
                z = seg_start_pos[2] + t * (seg_end_pos[2] - seg_start_pos[2])

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

    def _point_near_road(
        self,
        point: Tuple[float, float],
        vertices: List[Tuple[float, float, float]],
        road_width: float,
    ) -> bool:
        """Check if a point is near a road segment."""
        px, py = point
        half_width = road_width / 2 + 5.0  # Extra margin

        for i in range(len(vertices) - 1):
            x1, y1 = vertices[i][0], vertices[i][1]
            x2, y2 = vertices[i + 1][0], vertices[i + 1][1]

            # Distance from point to line segment
            dist = self._point_to_segment_distance(px, py, x1, y1, x2, y2)
            if dist < half_width:
                return True

        return False

    def _point_to_segment_distance(
        self,
        px: float, py: float,
        x1: float, y1: float,
        x2: float, y2: float,
    ) -> float:
        """Calculate distance from point to line segment."""
        dx = x2 - x1
        dy = y2 - y1

        if dx == 0 and dy == 0:
            return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)

        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))

        proj_x = x1 + t * dx
        proj_y = y1 + t * dy

        return math.sqrt((px - proj_x) ** 2 + (py - proj_y) ** 2)

    def _create_furniture_at_intersection(
        self,
        furniture_type: FurnitureType,
        intersection_pos: Tuple[float, float, float],
        road_vertices: List[Tuple[float, float, float]],
        config: FurnitureDistribution,
    ) -> Optional[StreetFurniture]:
        """Create furniture at an intersection."""
        # Find nearest road point to determine orientation
        min_dist = float('inf')
        nearest_dir = (1.0, 0.0)

        for i in range(len(road_vertices) - 1):
            x1, y1 = road_vertices[i][0], road_vertices[i][1]
            x2, y2 = road_vertices[i + 1][0], road_vertices[i + 1][1]

            dist = self._point_to_segment_distance(
                intersection_pos[0], intersection_pos[1], x1, y1, x2, y2
            )

            if dist < min_dist:
                min_dist = dist
                dx, dy = x2 - x1, y2 - y1
                length = math.sqrt(dx * dx + dy * dy)
                if length > 0.001:
                    nearest_dir = (dx / length, dy / length)

        rotation = math.atan2(nearest_dir[1], nearest_dir[0])

        return StreetFurniture(
            furniture_type=furniture_type,
            position=intersection_pos,
            rotation=rotation,
        )


__all__ = [
    "FurnitureType",
    "StreetFurniture",
    "FurnitureDistribution",
    "FURNITURE_DISTRIBUTIONS",
    "ManholePlacer",
    "FurnitureDistributor",
]
