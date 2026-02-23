"""
Street Lighting System

Urban street lighting with photometric accuracy.
Provides various fixture types and placement strategies.

Implements REQ-UR-05: Street Lighting System.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum
import math


class LuminaireType(Enum):
    """Luminaire fixture types."""
    COBRA_HEAD = "cobra_head"
    DECORATIVE = "decorative"
    SHOEBOX = "shoebox"
    POST_TOP = "post_top"
    SUSPENDED = "suspended"
    WALL_MOUNTED = "wall_mounted"
    HIGH_MAST = "high_mast"
    BOLLARD = "bollard"
    ACORN = "acorn"
    GLOBE = "globe"


class LightSource(Enum):
    """Light source technologies."""
    LED = "led"
    HIGH_PRESSURE_SODIUM = "hps"
    METAL_HALIDE = "mh"
    INDUCTION = "induction"
    FLUORESCENT = "fluorescent"
    INCANDESCENT = "incandescent"


class PoleMaterial(Enum):
    """Pole material types."""
    STEEL = "steel"
    ALUMINUM = "aluminum"
    CONCRETE = "concrete"
    FIBERGLASS = "fiberglass"
    WOOD = "wood"
    CAST_IRON = "cast_iron"


class LightDistribution(Enum):
    """IESNA light distribution types."""
    TYPE_I = "type_i"       # Two-way, narrow
    TYPE_II = "type_ii"     # Two-way, medium
    TYPE_III = "type_iii"   # Two-way, wide
    TYPE_IV = "type_iv"     # Four-way, asymmetrical
    TYPE_V = "type_v"       # Circular, symmetrical
    TYPE_VS = "type_vs"     # Square, symmetrical


@dataclass
class PhotometricSpec:
    """
    Photometric specification for luminaire.

    Attributes:
        initial_lumens: Initial lumen output
        lumen_maintenance: Lumen maintenance factor at 20,000 hrs
        color_temperature: Correlated color temperature in Kelvin
        cri: Color rendering index (0-100)
        beam_angle: Primary beam angle in degrees
        cutoff_type: Cutoff classification
        distribution_type: IESNA distribution type
        BUG_rating: Backlight-Uplight-Glare rating (B-U-G)
    """
    initial_lumens: int = 10000
    lumen_maintenance: float = 0.9
    color_temperature: int = 4000
    cri: int = 70
    beam_angle: float = 120.0
    cutoff_type: str = "full_cutoff"
    distribution_type: str = "type_iii"
    BUG_rating: str = "B2-U0-G1"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "initial_lumens": self.initial_lumens,
            "lumen_maintenance": self.lumen_maintenance,
            "color_temperature": self.color_temperature,
            "cri": self.cri,
            "beam_angle": self.beam_angle,
            "cutoff_type": self.cutoff_type,
            "distribution_type": self.distribution_type,
            "BUG_rating": self.BUG_rating,
        }

    @property
    def maintained_lumens(self) -> float:
        """Get maintained lumen output."""
        return self.initial_lumens * self.lumen_maintenance


@dataclass
class LuminaireSpec:
    """
    Complete luminaire specification.

    Attributes:
        luminaire_id: Unique luminaire identifier
        name: Luminaire name
        luminaire_type: Fixture type
        light_source: Light source technology
        photometrics: Photometric specifications
        wattage: Power consumption in watts
        voltage: Operating voltage
        height: Luminaire mounting height in meters
        overhang: Overhang from pole in meters
        tilt: Tilt angle in degrees
        weight: Fixture weight in kg
        material: Housing material
        finish: Color/finish
    """
    luminaire_id: str = ""
    name: str = ""
    luminaire_type: str = "cobra_head"
    light_source: str = "led"
    photometrics: Optional[PhotometricSpec] = None
    wattage: int = 100
    voltage: int = 120
    height: float = 8.0
    overhang: float = 0.5
    tilt: float = 0.0
    weight: float = 10.0
    material: str = "aluminum"
    finish: str = "dark_bronze"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "luminaire_id": self.luminaire_id,
            "name": self.name,
            "luminaire_type": self.luminaire_type,
            "light_source": self.light_source,
            "photometrics": self.photometrics.to_dict() if self.photometrics else None,
            "wattage": self.wattage,
            "voltage": self.voltage,
            "height": self.height,
            "overhang": self.overhang,
            "tilt": self.tilt,
            "weight": self.weight,
            "material": self.material,
            "finish": self.finish,
        }


@dataclass
class PoleSpec:
    """
    Street light pole specification.

    Attributes:
        pole_id: Unique pole identifier
        pole_type: Pole type (single, double, mast_arm, etc.)
        material: Pole material
        height: Total pole height in meters
        base_diameter: Base diameter in meters
        top_diameter: Top diameter in meters
        base_type: Base type (embedded, anchor base, etc.)
        arm_length: Mast arm length in meters
        arm_type: Arm type (single, twin, etc.)
        color: Pole color
        has_base_cabinet: Has electrical cabinet at base
    """
    pole_id: str = ""
    pole_type: str = "single"
    material: str = "steel"
    height: float = 9.0
    base_diameter: float = 0.25
    top_diameter: float = 0.15
    base_type: str = "anchor_base"
    arm_length: float = 1.5
    arm_type: str = "single"
    color: str = "#444444"
    has_base_cabinet: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pole_id": self.pole_id,
            "pole_type": self.pole_type,
            "material": self.material,
            "height": self.height,
            "base_diameter": self.base_diameter,
            "top_diameter": self.top_diameter,
            "base_type": self.base_type,
            "arm_length": self.arm_length,
            "arm_type": self.arm_type,
            "color": self.color,
            "has_base_cabinet": self.has_base_cabinet,
        }


@dataclass
class StreetLightInstance:
    """
    Placed street light instance.

    Attributes:
        instance_id: Unique instance identifier
        luminaire: Luminaire specification
        pole: Pole specification
        position: Position (x, y, z)
        rotation: Rotation angle in degrees
        aim_direction: Direction luminaire is aimed
        spacing_from_previous: Distance from previous light
        circuit_id: Electrical circuit ID
    """
    instance_id: str = ""
    luminaire: Optional[LuminaireSpec] = None
    pole: Optional[PoleSpec] = None
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: float = 0.0
    aim_direction: float = 0.0
    spacing_from_previous: float = 30.0
    circuit_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "instance_id": self.instance_id,
            "luminaire": self.luminaire.to_dict() if self.luminaire else None,
            "pole": self.pole.to_dict() if self.pole else None,
            "position": list(self.position),
            "rotation": self.rotation,
            "aim_direction": self.aim_direction,
            "spacing_from_previous": self.spacing_from_previous,
            "circuit_id": self.circuit_id,
        }


# =============================================================================
# STANDARD LUMINAIRES
# =============================================================================

LUMINAIRE_CATALOG: Dict[str, LuminaireSpec] = {
    # LED Cobra Heads
    "LED-COBRA-100W": LuminaireSpec(
        luminaire_id="LED-COBRA-100W",
        name="LED Cobra Head 100W",
        luminaire_type="cobra_head",
        light_source="led",
        photometrics=PhotometricSpec(
            initial_lumens=14000,
            lumen_maintenance=0.92,
            color_temperature=4000,
            cri=70,
            beam_angle=120,
            cutoff_type="full_cutoff",
            distribution_type="type_iii",
            BUG_rating="B2-U0-G1",
        ),
        wattage=100,
        voltage=120,
        height=8.0,
        overhang=0.5,
        weight=8.5,
        material="aluminum",
        finish="dark_bronze",
    ),
    "LED-COBRA-150W": LuminaireSpec(
        luminaire_id="LED-COBRA-150W",
        name="LED Cobra Head 150W",
        luminaire_type="cobra_head",
        light_source="led",
        photometrics=PhotometricSpec(
            initial_lumens=21000,
            lumen_maintenance=0.92,
            color_temperature=4000,
            cri=70,
            beam_angle=120,
            cutoff_type="full_cutoff",
            distribution_type="type_iii",
            BUG_rating="B2-U0-G2",
        ),
        wattage=150,
        voltage=120,
        height=10.0,
        overhang=0.6,
        weight=10.0,
        material="aluminum",
        finish="dark_bronze",
    ),
    "LED-COBRA-250W": LuminaireSpec(
        luminaire_id="LED-COBRA-250W",
        name="LED Cobra Head 250W",
        luminaire_type="cobra_head",
        light_source="led",
        photometrics=PhotometricSpec(
            initial_lumens=35000,
            lumen_maintenance=0.92,
            color_temperature=4000,
            cri=70,
            beam_angle=130,
            cutoff_type="full_cutoff",
            distribution_type="type_iii",
            BUG_rating="B3-U0-G2",
        ),
        wattage=250,
        voltage=277,
        height=12.0,
        overhang=0.8,
        weight=14.0,
        material="aluminum",
        finish="dark_bronze",
    ),

    # LED Shoebox (Area)
    "LED-SHOEBOX-200W": LuminaireSpec(
        luminaire_id="LED-SHOEBOX-200W",
        name="LED Shoebox 200W",
        luminaire_type="shoebox",
        light_source="led",
        photometrics=PhotometricSpec(
            initial_lumens=28000,
            lumen_maintenance=0.92,
            color_temperature=5000,
            cri=70,
            beam_angle=110,
            cutoff_type="full_cutoff",
            distribution_type="type_v",
            BUG_rating="B3-U0-G2",
        ),
        wattage=200,
        voltage=277,
        height=12.0,
        overhang=0.0,
        weight=12.0,
        material="aluminum",
        finish="gray",
    ),

    # LED Post Top (Decorative)
    "LED-POSTTOP-60W": LuminaireSpec(
        luminaire_id="LED-POSTTOP-60W",
        name="LED Post Top 60W",
        luminaire_type="post_top",
        light_source="led",
        photometrics=PhotometricSpec(
            initial_lumens=7500,
            lumen_maintenance=0.90,
            color_temperature=3000,
            cri=80,
            beam_angle=180,
            cutoff_type="semi_cutoff",
            distribution_type="type_v",
            BUG_rating="B3-U2-G2",
        ),
        wattage=60,
        voltage=120,
        height=4.5,
        overhang=0.0,
        weight=6.0,
        material="aluminum",
        finish="black",
    ),
    "LED-ACORN-50W": LuminaireSpec(
        luminaire_id="LED-ACORN-50W",
        name="LED Acorn 50W",
        luminaire_type="acorn",
        light_source="led",
        photometrics=PhotometricSpec(
            initial_lumens=5500,
            lumen_maintenance=0.90,
            color_temperature=2700,
            cri=80,
            beam_angle=360,
            cutoff_type="non_cutoff",
            distribution_type="type_v",
            BUG_rating="B3-U4-G3",
        ),
        wattage=50,
        voltage=120,
        height=4.0,
        overhang=0.0,
        weight=8.0,
        material="cast_aluminum",
        finish="black",
    ),

    # LED High Mast
    "LED-HIGHMAST-400W": LuminaireSpec(
        luminaire_id="LED-HIGHMAST-400W",
        name="LED High Mast 400W",
        luminaire_type="high_mast",
        light_source="led",
        photometrics=PhotometricSpec(
            initial_lumens=56000,
            lumen_maintenance=0.92,
            color_temperature=4000,
            cri=70,
            beam_angle=100,
            cutoff_type="full_cutoff",
            distribution_type="type_v",
            BUG_rating="B4-U0-G3",
        ),
        wattage=400,
        voltage=277,
        height=25.0,
        overhang=0.0,
        weight=25.0,
        material="aluminum",
        finish="gray",
    ),

    # LED Bollard
    "LED-BOLLARD-15W": LuminaireSpec(
        luminaire_id="LED-BOLLARD-15W",
        name="LED Bollard 15W",
        luminaire_type="bollard",
        light_source="led",
        photometrics=PhotometricSpec(
            initial_lumens=1800,
            lumen_maintenance=0.90,
            color_temperature=3000,
            cri=80,
            beam_angle=180,
            cutoff_type="full_cutoff",
            distribution_type="type_v",
            BUG_rating="B1-U0-G0",
        ),
        wattage=15,
        voltage=120,
        height=1.0,
        overhang=0.0,
        weight=5.0,
        material="aluminum",
        finish="dark_bronze",
    ),

    # Legacy HPS
    "HPS-COBRA-150W": LuminaireSpec(
        luminaire_id="HPS-COBRA-150W",
        name="HPS Cobra Head 150W",
        luminaire_type="cobra_head",
        light_source="hps",
        photometrics=PhotometricSpec(
            initial_lumens=16000,
            lumen_maintenance=0.85,
            color_temperature=2100,
            cri=25,
            beam_angle=130,
            cutoff_type="full_cutoff",
            distribution_type="type_iii",
            BUG_rating="B2-U1-G2",
        ),
        wattage=150,
        voltage=120,
        height=8.0,
        overhang=0.5,
        weight=12.0,
        material="aluminum",
        finish="dark_bronze",
    ),
}

# =============================================================================
# STANDARD POLES
# =============================================================================

POLE_CATALOG: Dict[str, PoleSpec] = {
    "POLE-STEEL-9M": PoleSpec(
        pole_id="POLE-STEEL-9M",
        pole_type="single",
        material="steel",
        height=9.0,
        base_diameter=0.25,
        top_diameter=0.15,
        base_type="anchor_base",
        arm_length=1.5,
        arm_type="single",
        color="#444444",
        has_base_cabinet=True,
    ),
    "POLE-STEEL-12M": PoleSpec(
        pole_id="POLE-STEEL-12M",
        pole_type="single",
        material="steel",
        height=12.0,
        base_diameter=0.30,
        top_diameter=0.18,
        base_type="anchor_base",
        arm_length=2.0,
        arm_type="single",
        color="#444444",
        has_base_cabinet=True,
    ),
    "POLE-STEEL-DOUBLE-9M": PoleSpec(
        pole_id="POLE-STEEL-DOUBLE-9M",
        pole_type="double",
        material="steel",
        height=9.0,
        base_diameter=0.30,
        top_diameter=0.18,
        base_type="anchor_base",
        arm_length=1.5,
        arm_type="twin",
        color="#444444",
        has_base_cabinet=True,
    ),
    "POLE-ALUM-POST-4M": PoleSpec(
        pole_id="POLE-ALUM-POST-4M",
        pole_type="post_top",
        material="aluminum",
        height=4.0,
        base_diameter=0.15,
        top_diameter=0.12,
        base_type="anchor_base",
        arm_length=0.0,
        arm_type="none",
        color="#1a1a1a",
        has_base_cabinet=False,
    ),
    "POLE-ALUM-DECORATIVE-4M": PoleSpec(
        pole_id="POLE-ALUM-DECORATIVE-4M",
        pole_type="post_top",
        material="aluminum",
        height=4.5,
        base_diameter=0.18,
        top_diameter=0.10,
        base_type="anchor_base",
        arm_length=0.0,
        arm_type="none",
        color="#1a1a1a",
        has_base_cabinet=False,
    ),
    "POLE-CONCRETE-12M": PoleSpec(
        pole_id="POLE-CONCRETE-12M",
        pole_type="single",
        material="concrete",
        height=12.0,
        base_diameter=0.35,
        top_diameter=0.20,
        base_type="embedded",
        arm_length=2.5,
        arm_type="single",
        color="#888888",
        has_base_cabinet=True,
    ),
    "POLE-MAST-ARM-9M": PoleSpec(
        pole_id="POLE-MAST-ARM-9M",
        pole_type="mast_arm",
        material="steel",
        height=9.0,
        base_diameter=0.30,
        top_diameter=0.18,
        base_type="anchor_base",
        arm_length=4.0,
        arm_type="single",
        color="#444444",
        has_base_cabinet=True,
    ),
    "POLE-HIGH-MAST-25M": PoleSpec(
        pole_id="POLE-HIGH-MAST-25M",
        pole_type="high_mast",
        material="steel",
        height=25.0,
        base_diameter=0.60,
        top_diameter=0.35,
        base_type="anchor_base",
        arm_length=0.0,
        arm_type="ring",
        color="#666666",
        has_base_cabinet=True,
    ),
}


class LightingPlacer:
    """
    Places street lights along road network.

    Follows IESNA RP-8 recommendations for spacing and positioning.

    Usage:
        placer = LightingPlacer()
        lights = placer.place_along_road(road_segments, "collector")
    """

    # Recommended spacing by road type (in meters)
    ROAD_SPACING = {
        "highway": 60.0,
        "arterial": 45.0,
        "collector": 35.0,
        "local": 30.0,
        "residential": 40.0,
        "alley": 25.0,
    }

    # Recommended luminaire by road type
    ROAD_LUMINAIRE = {
        "highway": "LED-COBRA-250W",
        "arterial": "LED-COBRA-150W",
        "collector": "LED-COBRA-100W",
        "local": "LED-COBRA-100W",
        "residential": "LED-COBRA-100W",
        "alley": "LED-COBRA-100W",
    }

    # Recommended pole by road type
    ROAD_POLE = {
        "highway": "POLE-STEEL-12M",
        "arterial": "POLE-STEEL-9M",
        "collector": "POLE-STEEL-9M",
        "local": "POLE-STEEL-9M",
        "residential": "POLE-STEEL-9M",
        "alley": "POLE-STEEL-9M",
    }

    def __init__(self):
        """Initialize lighting placer."""
        self.luminaire_catalog = LUMINAIRE_CATALOG
        self.pole_catalog = POLE_CATALOG

    def place_along_road(
        self,
        road_segments: List[Tuple[Tuple[float, float], Tuple[float, float]]],
        road_type: str = "collector",
        offset: float = 2.0,
        stagger: bool = True,
        road_width: float = 10.0,
    ) -> List[StreetLightInstance]:
        """
        Place lights along a road.

        Args:
            road_segments: List of (start, end) point tuples
            road_type: Type of road for spacing/luminaire selection
            offset: Offset from road edge in meters
            stagger: Whether to stagger lights (alternating sides)
            road_width: Width of road in meters

        Returns:
            List of StreetLightInstance
        """
        lights = []

        spacing = self.ROAD_SPACING.get(road_type, 35.0)
        luminaire_id = self.ROAD_LUMINAIRE.get(road_type, "LED-COBRA-100W")
        pole_id = self.ROAD_POLE.get(road_type, "POLE-STEEL-9M")

        luminaire = self.luminaire_catalog.get(luminaire_id)
        pole = self.pole_catalog.get(pole_id)

        if not luminaire or not pole:
            return lights

        # Calculate total road length and positions
        distance = 0.0
        accumulated_segments = []

        for start, end in road_segments:
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            length = math.sqrt(dx * dx + dy * dy)
            accumulated_segments.append((start, end, distance, distance + length))
            distance += length

        # Place lights at intervals
        current_distance = spacing / 2  # Start with offset
        side = 0

        while current_distance < distance:
            # Find segment containing this position
            for start, end, seg_start, seg_end in accumulated_segments:
                if seg_start <= current_distance < seg_end:
                    # Interpolate position
                    t = (current_distance - seg_start) / (seg_end - seg_start)
                    x = start[0] + (end[0] - start[0]) * t
                    y = start[1] + (end[1] - start[1]) * t

                    # Calculate direction
                    dx = end[0] - start[0]
                    dy = end[1] - start[1]
                    angle = math.degrees(math.atan2(dy, dx))

                    # Offset perpendicular to road
                    if stagger:
                        side_offset = offset if side % 2 == 0 else road_width + offset
                        side += 1
                    else:
                        side_offset = offset

                    perp_angle = angle + 90
                    ox = side_offset * math.cos(math.radians(perp_angle))
                    oy = side_offset * math.sin(math.radians(perp_angle))

                    # Create light instance
                    light = StreetLightInstance(
                        instance_id=f"light_{len(lights)}",
                        luminaire=luminaire,
                        pole=pole,
                        position=(x + ox, y + oy, 0),
                        rotation=angle,
                        aim_direction=angle if side % 2 == 0 else angle + 180,
                        spacing_from_previous=spacing if lights else 0,
                    )
                    lights.append(light)
                    break

            current_distance += spacing

        return lights

    def place_at_intersection(
        self,
        position: Tuple[float, float, float],
        intersection_type: str = "4way",
        road_widths: List[float] = None,
    ) -> List[StreetLightInstance]:
        """
        Place lights at intersection.

        Args:
            position: Intersection center position
            position: Intersection type (4way, 3way, roundabout)
            road_widths: Widths of approaching roads

        Returns:
            List of StreetLightInstance
        """
        lights = []
        x, y, z = position

        luminaire = self.luminaire_catalog.get("LED-COBRA-100W")
        pole = self.pole_catalog.get("POLE-STEEL-9M")

        if not luminaire or not pole:
            return lights

        if intersection_type == "4way" or intersection_type == "intersection_4way":
            # Four corners
            for i, angle in enumerate([45, 135, 225, 315]):
                rad = math.radians(angle)
                offset = 3.0
                lx = x + offset * math.cos(rad)
                ly = y + offset * math.sin(rad)

                light = StreetLightInstance(
                    instance_id=f"int_light_{i}",
                    luminaire=luminaire,
                    pole=pole,
                    position=(lx, ly, z),
                    rotation=angle - 45,
                    aim_direction=angle - 45,
                )
                lights.append(light)

        elif intersection_type == "3way" or intersection_type == "intersection_3way":
            # Three corners
            for i, angle in enumerate([30, 150, 270]):
                rad = math.radians(angle)
                offset = 3.0
                lx = x + offset * math.cos(rad)
                ly = y + offset * math.sin(rad)

                light = StreetLightInstance(
                    instance_id=f"int_light_{i}",
                    luminaire=luminaire,
                    pole=pole,
                    position=(lx, ly, z),
                    rotation=angle - 90,
                    aim_direction=angle - 90,
                )
                lights.append(light)

        elif intersection_type == "roundabout":
            # Central feature + approaches
            for i, angle in enumerate([0, 90, 180, 270]):
                rad = math.radians(angle)
                offset = 12.0
                lx = x + offset * math.cos(rad)
                ly = y + offset * math.sin(rad)

                light = StreetLightInstance(
                    instance_id=f"rabout_light_{i}",
                    luminaire=luminaire,
                    pole=pole,
                    position=(lx, ly, z),
                    rotation=angle + 180,
                    aim_direction=angle + 180,
                )
                lights.append(light)

        return lights

    def place_pedestrian_lighting(
        self,
        path_segments: List[Tuple[Tuple[float, float], Tuple[float, float]]],
        spacing: float = 15.0,
    ) -> List[StreetLightInstance]:
        """
        Place pedestrian-scale lighting along path.

        Args:
            path_segments: List of (start, end) point tuples
            spacing: Distance between lights

        Returns:
            List of StreetLightInstance
        """
        lights = []

        luminaire = self.luminaire_catalog.get("LED-POSTTOP-60W")
        pole = self.pole_catalog.get("POLE-ALUM-POST-4M")

        if not luminaire or not pole:
            return lights

        distance = 0.0

        for start, end in path_segments:
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            length = math.sqrt(dx * dx + dy * dy)
            angle = math.degrees(math.atan2(dy, dx))

            # Place at intervals along segment
            current = spacing / 2
            while current < length:
                t = current / length
                x = start[0] + (end[0] - start[0]) * t
                y = start[1] + (end[1] - start[1]) * t

                light = StreetLightInstance(
                    instance_id=f"ped_light_{len(lights)}",
                    luminaire=luminaire,
                    pole=pole,
                    position=(x, y, 0),
                    rotation=angle,
                    aim_direction=0,
                )
                lights.append(light)

                current += spacing

            distance += length

        return lights


def create_lighting_placer() -> LightingPlacer:
    """Convenience function to create lighting placer."""
    return LightingPlacer()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "LuminaireType",
    "LightSource",
    "PoleMaterial",
    "LightDistribution",
    "PhotometricSpec",
    "LuminaireSpec",
    "PoleSpec",
    "StreetLightInstance",
    "LUMINAIRE_CATALOG",
    "POLE_CATALOG",
    "LightingPlacer",
    "create_lighting_placer",
]
