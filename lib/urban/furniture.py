"""
Urban Furniture System

Street furniture including benches, bollards, planters, trash receptacles,
bike racks, and other urban amenities.

Implements REQ-UR-06: Urban Furniture.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum
import math


class FurnitureCategory(Enum):
    """Urban furniture categories."""
    SEATING = "seating"
    BOLLARD = "bollard"
    PLANTER = "planter"
    TRASH_RECEPTACLE = "trash_receptacle"
    BIKE_RACK = "bike_rack"
    BUS_SHELTER = "bus_shelter"
    KIOSK = "kiosk"
    NEWSRACK = "newsrack"
    BENCH = "bench"
    TABLE = "table"
    DRINKING_FOUNTAIN = "drinking_fountain"
    MAILBOX = "mailbox"
    FIRE_HYDRANT = "fire_hydrant"
    UTILITY_BOX = "utility_box"
    TRAFFIC_BOX = "traffic_box"
    METER = "meter"
    SIGN_POST = "sign_post"
    FLAGPOLE = "flagpole"
    CLOCK = "clock"
    MEMORIAL = "memorial"


class FurnitureMaterial(Enum):
    """Furniture materials."""
    STEEL = "steel"
    ALUMINUM = "aluminum"
    CAST_IRON = "cast_iron"
    CONCRETE = "concrete"
    WOOD = "wood"
    RECYCLED_PLASTIC = "recycled_plastic"
    GRANITE = "granite"
    BRONZE = "bronze"
    STAINLESS_STEEL = "stainless_steel"
    COMBINATION = "combination"


class MountingType(Enum):
    """Furniture mounting types."""
    SURFACE_MOUNTED = "surface_mounted"
    EMBEDDED = "embedded"
    FREESTANDING = "freestanding"
    WALL_MOUNTED = "wall_mounted"
    POST_MOUNTED = "post_mounted"


@dataclass
class FurnitureSpec:
    """
    Furniture specification.

    Attributes:
        furniture_id: Unique furniture identifier
        name: Furniture name
        category: Furniture category
        materials: List of materials
        width: Width in meters
        depth: Depth in meters
        height: Height in meters
        weight: Weight in kg
        color: Primary color
        finish: Surface finish
        mounting: Mounting type
        has_back: Whether seating has backrest
        capacity: Seating/holding capacity
        manufacturer: Manufacturer name
        model_number: Model number
        accessibility_compliant: ADA compliant
        is_vandal_resistant: Vandal-resistant construction
    """
    furniture_id: str = ""
    name: str = ""
    category: str = "bench"
    materials: List[str] = field(default_factory=list)
    width: float = 1.5
    depth: float = 0.5
    height: float = 0.5
    weight: float = 50.0
    color: str = "#4a4a4a"
    finish: str = "powder_coat"
    mounting: str = "surface_mounted"
    has_back: bool = True
    capacity: int = 2
    manufacturer: str = ""
    model_number: str = ""
    accessibility_compliant: bool = True
    is_vandal_resistant: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "furniture_id": self.furniture_id,
            "name": self.name,
            "category": self.category,
            "materials": self.materials,
            "width": self.width,
            "depth": self.depth,
            "height": self.height,
            "weight": self.weight,
            "color": self.color,
            "finish": self.finish,
            "mounting": self.mounting,
            "has_back": self.has_back,
            "capacity": self.capacity,
            "manufacturer": self.manufacturer,
            "model_number": self.model_number,
            "accessibility_compliant": self.accessibility_compliant,
            "is_vandal_resistant": self.is_vandal_resistant,
        }


@dataclass
class FurnitureInstance:
    """
    Placed furniture instance.

    Attributes:
        instance_id: Unique instance identifier
        spec: Furniture specification
        position: Position (x, y, z)
        rotation: Rotation angle in degrees
        zone: Placement zone (sidewalk, plaza, park, etc.)
    """
    instance_id: str = ""
    spec: Optional[FurnitureSpec] = None
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: float = 0.0
    zone: str = "sidewalk"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "instance_id": self.instance_id,
            "spec": self.spec.to_dict() if self.spec else None,
            "position": list(self.position),
            "rotation": self.rotation,
            "zone": self.zone,
        }


# =============================================================================
# FURNITURE CATALOG
# =============================================================================

BENCH_CATALOG: Dict[str, FurnitureSpec] = {
    "BENCH-CLASSIC-6FT": FurnitureSpec(
        furniture_id="BENCH-CLASSIC-6FT",
        name="Classic Park Bench 6ft",
        category="bench",
        materials=["cast_iron", "wood"],
        width=1.83,
        depth=0.65,
        height=0.85,
        weight=90.0,
        color="#4a4a4a",
        finish="powder_coat",
        mounting="surface_mounted",
        has_back=True,
        capacity=3,
        manufacturer="DuMor",
        model_number="33-6M",
    ),
    "BENCH-MODERN-4FT": FurnitureSpec(
        furniture_id="BENCH-MODERN-4FT",
        name="Modern Bench 4ft",
        category="bench",
        materials=["steel", "recycled_plastic"],
        width=1.22,
        depth=0.55,
        height=0.80,
        weight=45.0,
        color="#2c3e50",
        finish="powder_coat",
        mounting="embedded",
        has_back=True,
        capacity=2,
        manufacturer="Landscape Forms",
        model_number="LFI-200",
    ),
    "BENCH-BACKLESS-6FT": FurnitureSpec(
        furniture_id="BENCH-BACKLESS-6FT",
        name="Backless Bench 6ft",
        category="bench",
        materials=["aluminum"],
        width=1.83,
        depth=0.45,
        height=0.45,
        weight=35.0,
        color="#555555",
        finish="anodized",
        mounting="surface_mounted",
        has_back=False,
        capacity=3,
        manufacturer="Victor Stanley",
        model_number="VS-445",
    ),
    "BENCH-CONCRETE-8FT": FurnitureSpec(
        furniture_id="BENCH-CONCRETE-8FT",
        name="Concrete Bench 8ft",
        category="bench",
        materials=["concrete"],
        width=2.44,
        depth=0.50,
        height=0.45,
        weight=350.0,
        color="#808080",
        finish="exposed_aggregate",
        mounting="freestanding",
        has_back=False,
        capacity=4,
        manufacturer="Wausau Tile",
        model_number="WT-CB8",
    ),
}

BOLLARD_CATALOG: Dict[str, FurnitureSpec] = {
    "BOLLARD-STEEL-FIXED": FurnitureSpec(
        furniture_id="BOLLARD-STEEL-FIXED",
        name="Steel Fixed Bollard",
        category="bollard",
        materials=["steel"],
        width=0.15,
        depth=0.15,
        height=0.90,
        weight=25.0,
        color="#1a1a1a",
        finish="powder_coat",
        mounting="embedded",
        capacity=0,
        is_vandal_resistant=True,
    ),
    "BOLLARD-REMOVABLE": FurnitureSpec(
        furniture_id="BOLLARD-REMOVABLE",
        name="Removable Bollard",
        category="bollard",
        materials=["stainless_steel"],
        width=0.12,
        depth=0.12,
        height=0.90,
        weight=15.0,
        color="#c0c0c0",
        finish="brushed",
        mounting="surface_mounted",
        capacity=0,
        is_vandal_resistant=True,
    ),
    "BOLLARD-CONCRETE": FurnitureSpec(
        furniture_id="BOLLARD-CONCRETE",
        name="Concrete Bollard",
        category="bollard",
        materials=["concrete"],
        width=0.30,
        depth=0.30,
        height=0.90,
        weight=80.0,
        color="#808080",
        finish="smooth",
        mounting="embedded",
        capacity=0,
        is_vandal_resistant=True,
    ),
    "BOLLARD-LIGHTED": FurnitureSpec(
        furniture_id="BOLLARD-LIGHTED",
        name="Lighted Bollard",
        category="bollard",
        materials=["aluminum", "polycarbonate"],
        width=0.20,
        depth=0.20,
        height=1.0,
        weight=12.0,
        color="#2c3e50",
        finish="powder_coat",
        mounting="embedded",
        capacity=0,
        is_vandal_resistant=True,
    ),
}

PLANTER_CATALOG: Dict[str, FurnitureSpec] = {
    "PLANTER-SQUARE-M": FurnitureSpec(
        furniture_id="PLANTER-SQUARE-M",
        name="Square Planter Medium",
        category="planter",
        materials=["concrete"],
        width=0.60,
        depth=0.60,
        height=0.50,
        weight=75.0,
        color="#696969",
        finish="smooth",
        mounting="freestanding",
        capacity=1,
    ),
    "PLANTER-ROUND-L": FurnitureSpec(
        furniture_id="PLANTER-ROUND-L",
        name="Round Planter Large",
        category="planter",
        materials=["fiberglass"],
        width=0.90,
        depth=0.90,
        height=0.75,
        weight=25.0,
        color="#8b4513",
        finish="textured",
        mounting="freestanding",
        capacity=1,
    ),
    "PLANTER-RECT-L": FurnitureSpec(
        furniture_id="PLANTER-RECT-L",
        name="Rectangular Planter Large",
        category="planter",
        materials=["steel"],
        width=1.50,
        depth=0.50,
        height=0.60,
        weight=60.0,
        color="#2f4f4f",
        finish="powder_coat",
        mounting="freestanding",
        capacity=2,
    ),
    "PLANTER-TREE-GRATE": FurnitureSpec(
        furniture_id="PLANTER-TREE-GRATE",
        name="Tree Grate Planter",
        category="planter",
        materials=["cast_iron"],
        width=1.50,
        depth=1.50,
        height=0.05,
        weight=100.0,
        color="#1a1a1a",
        finish="powder_coat",
        mounting="embedded",
        capacity=1,
    ),
}

TRASH_RECEPTACLE_CATALOG: Dict[str, FurnitureSpec] = {
    "TRASH-32-GAL": FurnitureSpec(
        furniture_id="TRASH-32-GAL",
        name="Trash Receptacle 32 Gallon",
        category="trash_receptacle",
        materials=["steel"],
        width=0.55,
        depth=0.55,
        height=0.90,
        weight=30.0,
        color="#2e4a2e",
        finish="powder_coat",
        mounting="surface_mounted",
        capacity=32,
        is_vandal_resistant=True,
    ),
    "TRASH-RECYCLE-DUAL": FurnitureSpec(
        furniture_id="TRASH-RECYCLE-DUAL",
        name="Dual Stream Recycle/Trash",
        category="trash_receptacle",
        materials=["aluminum"],
        width=1.0,
        depth=0.45,
        height=1.0,
        weight=40.0,
        color="#1a1a1a",
        finish="powder_coat",
        mounting="surface_mounted",
        capacity=25,
        is_vandal_resistant=True,
    ),
    "TRASH-ASHTRAY": FurnitureSpec(
        furniture_id="TRASH-ASHTRAY",
        name="Standing Ashtray",
        category="trash_receptacle",
        materials=["steel"],
        width=0.30,
        depth=0.30,
        height=0.90,
        weight=8.0,
        color="#1a1a1a",
        finish="powder_coat",
        mounting="surface_mounted",
        capacity=1,
        is_vandal_resistant=True,
    ),
}

BIKE_RACK_CATALOG: Dict[str, FurnitureSpec] = {
    "BIKE-U-RACK": FurnitureSpec(
        furniture_id="BIKE-U-RACK",
        name="U-Rack Bike Rack",
        category="bike_rack",
        materials=["steel"],
        width=0.90,
        depth=0.60,
        height=0.90,
        weight=20.0,
        color="#1a1a1a",
        finish="powder_coat",
        mounting="embedded",
        capacity=2,
    ),
    "BIKE-CORRAL-5": FurnitureSpec(
        furniture_id="BIKE-CORRAL-5",
        name="Bike Corral 5 Capacity",
        category="bike_rack",
        materials=["steel"],
        width=2.50,
        depth=0.90,
        height=0.90,
        weight=60.0,
        color="#2c3e50",
        finish="powder_coat",
        mounting="surface_mounted",
        capacity=5,
    ),
    "BIKE-WAVE-4": FurnitureSpec(
        furniture_id="BIKE-WAVE-4",
        name="Wave Rack 4 Bikes",
        category="bike_rack",
        materials=["steel"],
        width=2.0,
        depth=0.50,
        height=0.85,
        weight=40.0,
        color="#555555",
        finish="galvanized",
        mounting="surface_mounted",
        capacity=4,
    ),
}

BUS_SHELTER_CATALOG: Dict[str, FurnitureSpec] = {
    "SHELTER-TRANSIT-SM": FurnitureSpec(
        furniture_id="SHELTER-TRANSIT-SM",
        name="Transit Shelter Small",
        category="bus_shelter",
        materials=["steel", "tempered_glass"],
        width=2.50,
        depth=1.50,
        height=2.80,
        weight=200.0,
        color="#1a1a1a",
        finish="powder_coat",
        mounting="embedded",
        capacity=8,
        has_back=True,
    ),
    "SHELTER-TRANSIT-LG": FurnitureSpec(
        furniture_id="SHELTER-TRANSIT-LG",
        name="Transit Shelter Large",
        category="bus_shelter",
        materials=["aluminum", "tempered_glass"],
        width=4.50,
        depth=2.0,
        height=3.0,
        weight=350.0,
        color="#1a1a1a",
        finish="powder_coat",
        mounting="embedded",
        capacity=15,
        has_back=True,
    ),
}

UTILITY_CATALOG: Dict[str, FurnitureSpec] = {
    "UTILITY-ELECTRIC-SM": FurnitureSpec(
        furniture_id="UTILITY-ELECTRIC-SM",
        name="Electric Transformer Small",
        category="utility_box",
        materials=["steel"],
        width=0.60,
        depth=0.45,
        height=1.0,
        weight=80.0,
        color="#505050",
        finish="powder_coat",
        mounting="surface_mounted",
    ),
    "UTILITY-TRAFFIC-CTRL": FurnitureSpec(
        furniture_id="UTILITY-TRAFFIC-CTRL",
        name="Traffic Controller Cabinet",
        category="traffic_box",
        materials=["aluminum"],
        width=0.50,
        depth=0.35,
        height=1.5,
        weight=50.0,
        color="#2e8b57",
        finish="powder_coat",
        mounting="surface_mounted",
    ),
    "UTILITY-FIRE-HYDRANT": FurnitureSpec(
        furniture_id="UTILITY-FIRE-HYDRANT",
        name="Fire Hydrant",
        category="fire_hydrant",
        materials=["cast_iron"],
        width=0.25,
        depth=0.25,
        height=0.75,
        weight=75.0,
        color="#ff0000",
        finish="enamel",
        mounting="embedded",
    ),
    "UTILITY-MAILBOX": FurnitureSpec(
        furniture_id="UTILITY-MAILBOX",
        name="USPS Mailbox",
        category="mailbox",
        materials=["aluminum"],
        width=0.40,
        depth=0.50,
        height=1.20,
        weight=15.0,
        color="#003399",
        finish="powder_coat",
        mounting="surface_mounted",
    ),
    "UTILITY-METER": FurnitureSpec(
        furniture_id="UTILITY-METER",
        name="Parking Meter",
        category="meter",
        materials=["steel"],
        width=0.20,
        depth=0.20,
        height=1.50,
        weight=15.0,
        color="#505050",
        finish="powder_coat",
        mounting="embedded",
    ),
}

# Combined catalog
FURNITURE_CATALOG: Dict[str, FurnitureSpec] = {}
FURNITURE_CATALOG.update(BENCH_CATALOG)
FURNITURE_CATALOG.update(BOLLARD_CATALOG)
FURNITURE_CATALOG.update(PLANTER_CATALOG)
FURNITURE_CATALOG.update(TRASH_RECEPTACLE_CATALOG)
FURNITURE_CATALOG.update(BIKE_RACK_CATALOG)
FURNITURE_CATALOG.update(BUS_SHELTER_CATALOG)
FURNITURE_CATALOG.update(UTILITY_CATALOG)


class FurniturePlacer:
    """
    Places urban furniture along streets and in public spaces.

    Usage:
        placer = FurniturePlacer()
        placements = placer.place_along_sidewalk(sidewalk_path, zone_width)
    """

    def __init__(self):
        """Initialize furniture placer."""
        self.catalog = FURNITURE_CATALOG

    def get_furniture(self, furniture_id: str) -> Optional[FurnitureSpec]:
        """Get furniture specification by ID."""
        return self.catalog.get(furniture_id)

    def get_by_category(self, category: str) -> List[FurnitureSpec]:
        """Get all furniture in a category."""
        return [f for f in self.catalog.values() if f.category == category]

    def place_benches_along_path(
        self,
        path_segments: List[Tuple[Tuple[float, float], Tuple[float, float]]],
        spacing: float = 15.0,
        offset: float = 1.0,
        side: str = "right",
        bench_type: str = "BENCH-MODERN-4FT",
    ) -> List[FurnitureInstance]:
        """
        Place benches along a path.

        Args:
            path_segments: List of (start, end) point tuples
            spacing: Distance between benches
            offset: Offset from path edge
            side: Side of path (left, right, alternating)
            bench_type: Furniture ID for bench

        Returns:
            List of FurnitureInstance
        """
        placements = []
        bench = self.catalog.get(bench_type)

        if not bench:
            return placements

        distance = 0.0
        next_placement = spacing / 2
        side_index = 0

        for start, end in path_segments:
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            length = math.sqrt(dx * dx + dy * dy)
            angle = math.degrees(math.atan2(dy, dx))

            segment_start_dist = distance
            segment_end_dist = distance + length

            while next_placement < segment_end_dist:
                t = (next_placement - segment_start_dist) / length
                x = start[0] + (end[0] - start[0]) * t
                y = start[1] + (end[1] - start[1]) * t

                # Determine side
                if side == "alternating":
                    current_side = 1 if side_index % 2 == 0 else -1
                    side_index += 1
                elif side == "left":
                    current_side = -1
                else:
                    current_side = 1

                # Perpendicular offset
                perp_angle = angle + 90
                ox = offset * current_side * math.cos(math.radians(perp_angle))
                oy = offset * current_side * math.sin(math.radians(perp_angle))

                placement = FurnitureInstance(
                    instance_id=f"bench_{len(placements)}",
                    spec=bench,
                    position=(x + ox, y + oy, 0),
                    rotation=angle if current_side > 0 else angle + 180,
                    zone="sidewalk",
                )
                placements.append(placement)

                next_placement += spacing

            distance += length

        return placements

    def place_bollards_along_edge(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        spacing: float = 1.5,
        offset: float = 0.5,
        bollard_type: str = "BOLLARD-STEEL-FIXED",
    ) -> List[FurnitureInstance]:
        """
        Place bollards along an edge.

        Args:
            start: Start point
            end: End point
            spacing: Distance between bollards
            offset: Offset from edge
            bollard_type: Furniture ID for bollard

        Returns:
            List of FurnitureInstance
        """
        placements = []
        bollard = self.catalog.get(bollard_type)

        if not bollard:
            return placements

        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.sqrt(dx * dx + dy * dy)
        angle = math.degrees(math.atan2(dy, dx))

        # Perpendicular offset
        perp_angle = angle + 90
        ox = offset * math.cos(math.radians(perp_angle))
        oy = offset * math.sin(math.radians(perp_angle))

        # Place bollards
        num_bollards = int(length / spacing) + 1

        for i in range(num_bollards):
            t = i / max(num_bollards - 1, 1)
            x = start[0] + (end[0] - start[0]) * t + ox
            y = start[1] + (end[1] - start[1]) * t + oy

            placement = FurnitureInstance(
                instance_id=f"bollard_{len(placements)}",
                spec=bollard,
                position=(x, y, 0),
                rotation=0,
                zone="edge",
            )
            placements.append(placement)

        return placements

    def place_trash_receptacles(
        self,
        bench_placements: List[FurnitureInstance],
        spacing: float = 30.0,
        offset: float = 2.0,
        receptacle_type: str = "TRASH-32-GAL",
    ) -> List[FurnitureInstance]:
        """
        Place trash receptacles near benches.

        Args:
            bench_placements: Existing bench placements
            spacing: Minimum distance between receptacles
            offset: Distance from bench
            receptacle_type: Furniture ID for receptacle

        Returns:
            List of FurnitureInstance
        """
        placements = []
        receptacle = self.catalog.get(receptacle_type)

        if not receptacle:
            return placements

        last_position = None

        for bench in bench_placements:
            if last_position:
                dist = math.sqrt(
                    (bench.position[0] - last_position[0]) ** 2 +
                    (bench.position[1] - last_position[1]) ** 2
                )
                if dist < spacing:
                    continue

            # Place receptacle near bench
            angle = bench.rotation + 90
            ox = offset * math.cos(math.radians(angle))
            oy = offset * math.sin(math.radians(angle))

            placement = FurnitureInstance(
                instance_id=f"trash_{len(placements)}",
                spec=receptacle,
                position=(bench.position[0] + ox, bench.position[1] + oy, 0),
                rotation=0,
                zone="sidewalk",
            )
            placements.append(placement)
            last_position = bench.position

        return placements

    def place_bike_racks(
        self,
        corners: List[Tuple[float, float]],
        spacing: float = 50.0,
        rack_type: str = "BIKE-U-RACK",
    ) -> List[FurnitureInstance]:
        """
        Place bike racks at suitable locations.

        Args:
            corners: Potential placement corners
            spacing: Minimum distance between racks
            rack_type: Furniture ID for bike rack

        Returns:
            List of FurnitureInstance
        """
        placements = []
        rack = self.catalog.get(rack_type)

        if not rack:
            return placements

        placed_positions = []

        for corner in corners:
            # Check spacing from existing placements
            too_close = False
            for pos in placed_positions:
                dist = math.sqrt(
                    (corner[0] - pos[0]) ** 2 +
                    (corner[1] - pos[1]) ** 2
                )
                if dist < spacing:
                    too_close = True
                    break

            if not too_close:
                placement = FurnitureInstance(
                    instance_id=f"bike_rack_{len(placements)}",
                    spec=rack,
                    position=(corner[0], corner[1], 0),
                    rotation=0,
                    zone="sidewalk",
                )
                placements.append(placement)
                placed_positions.append(corner)

        return placements

    def place_planters(
        self,
        positions: List[Tuple[float, float]],
        planter_type: str = "PLANTER-SQUARE-M",
        rotation: float = 0.0,
    ) -> List[FurnitureInstance]:
        """
        Place planters at specified positions.

        Args:
            positions: List of (x, y) positions
            planter_type: Furniture ID for planter
            rotation: Rotation angle

        Returns:
            List of FurnitureInstance
        """
        placements = []
        planter = self.catalog.get(planter_type)

        if not planter:
            return placements

        for i, pos in enumerate(positions):
            placement = FurnitureInstance(
                instance_id=f"planter_{i}",
                spec=planter,
                position=(pos[0], pos[1], 0),
                rotation=rotation,
                zone="plaza",
            )
            placements.append(placement)

        return placements

    def place_bus_shelter(
        self,
        position: Tuple[float, float],
        direction: float = 0.0,
        shelter_type: str = "SHELTER-TRANSIT-SM",
    ) -> FurnitureInstance:
        """
        Place bus shelter at position.

        Args:
            position: (x, y) position
            direction: Direction shelter faces
            shelter_type: Furniture ID for shelter

        Returns:
            FurnitureInstance
        """
        shelter = self.catalog.get(shelter_type)

        if not shelter:
            return FurnitureInstance()

        return FurnitureInstance(
            instance_id=f"shelter_{position[0]:.0f}_{position[1]:.0f}",
            spec=shelter,
            position=(position[0], position[1], 0),
            rotation=direction,
            zone="transit",
        )

    def place_utilities(
        self,
        sidewalk_segments: List[Tuple[Tuple[float, float], Tuple[float, float]]],
        fire_hydrant_spacing: float = 150.0,
        utility_spacing: float = 100.0,
    ) -> List[FurnitureInstance]:
        """
        Place utility items along sidewalks.

        Args:
            sidewalk_segments: List of (start, end) tuples
            fire_hydrant_spacing: Spacing for fire hydrants
            utility_spacing: Spacing for utility boxes

        Returns:
            List of FurnitureInstance
        """
        placements = []

        hydrant = self.catalog.get("UTILITY-FIRE-HYDRANT")
        utility_box = self.catalog.get("UTILITY-ELECTRIC-SM")

        distance = 0.0
        next_hydrant = fire_hydrant_spacing / 2
        next_utility = utility_spacing / 3

        for start, end in sidewalk_segments:
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            length = math.sqrt(dx * dx + dy * dy)
            angle = math.degrees(math.atan2(dy, dx))

            # Offset from sidewalk
            offset = 0.3
            ox = offset * math.cos(math.radians(angle + 90))
            oy = offset * math.sin(math.radians(angle + 90))

            segment_start = distance
            segment_end = distance + length

            # Place fire hydrants
            while next_hydrant < segment_end and hydrant:
                t = (next_hydrant - segment_start) / length
                x = start[0] + (end[0] - start[0]) * t + ox
                y = start[1] + (end[1] - start[1]) * t + oy

                placement = FurnitureInstance(
                    instance_id=f"hydrant_{len(placements)}",
                    spec=hydrant,
                    position=(x, y, 0),
                    rotation=0,
                    zone="utility",
                )
                placements.append(placement)
                next_hydrant += fire_hydrant_spacing

            # Place utility boxes
            while next_utility < segment_end and utility_box:
                t = (next_utility - segment_start) / length
                x = start[0] + (end[0] - start[0]) * t + ox
                y = start[1] + (end[1] - start[1]) * t + oy

                placement = FurnitureInstance(
                    instance_id=f"utility_{len(placements)}",
                    spec=utility_box,
                    position=(x, y, 0),
                    rotation=angle,
                    zone="utility",
                )
                placements.append(placement)
                next_utility += utility_spacing

            distance += length

        return placements


def create_furniture_placer() -> FurniturePlacer:
    """Convenience function to create furniture placer."""
    return FurniturePlacer()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "FurnitureCategory",
    "FurnitureMaterial",
    "MountingType",
    "FurnitureSpec",
    "FurnitureInstance",
    "BENCH_CATALOG",
    "BOLLARD_CATALOG",
    "PLANTER_CATALOG",
    "TRASH_RECEPTACLE_CATALOG",
    "BIKE_RACK_CATALOG",
    "BUS_SHELTER_CATALOG",
    "UTILITY_CATALOG",
    "FURNITURE_CATALOG",
    "FurniturePlacer",
    "create_furniture_placer",
]
