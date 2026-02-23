"""
Interior Details

Moldings, fixtures, and interior detail system.
Adds architectural details to interior spaces.

Implements REQ-IL-08: Interior Detail System (moldings, wainscoting).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum

from .types import FloorPlan, Room


class MoldingType(Enum):
    """Molding type classification."""
    BASEBOARD = "baseboard"
    CROWN = "crown"
    CHAIR_RAIL = "chair_rail"
    PICTURE_RAIL = "picture_rail"
    PLATE_RAIL = "plate_rail"
    WAINSCOTING = "wainscoting"
    DOOR_CASING = "door_casing"
    WINDOW_CASING = "window_casing"
    CORNER_GUARD = "corner_guard"


class FixtureType(Enum):
    """Built-in fixture types."""
    CEILING_LIGHT = "ceiling_light"
    WALL_SCONCE = "wall_sconce"
    RECESSED_LIGHT = "recessed_light"
    CEILING_FAN = "ceiling_fan"
    VENT_COVER = "vent_cover"
    SWITCH_PLATE = "switch_plate"
    OUTLET_COVER = "outlet_cover"
    THERMOSTAT = "thermostat"
    SMOKE_DETECTOR = "smoke_detector"
    CO_DETECTOR = "co_detector"


@dataclass
class MoldingConfig:
    """
    Molding configuration.

    Attributes:
        molding_type: Type of molding
        height: Molding height in meters
        depth: Molding depth/projection in meters
        material: Material preset
        style: Style preset (colonial, modern, craftsman, etc.)
    """
    molding_type: str = "baseboard"
    height: float = 0.1
    depth: float = 0.02
    material: str = "wood_white"
    style: str = "modern"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "molding_type": self.molding_type,
            "height": self.height,
            "depth": self.depth,
            "material": self.material,
            "style": self.style,
        }


@dataclass
class FixtureConfig:
    """
    Fixture configuration.

    Attributes:
        fixture_type: Type of fixture
        position: Position (x, y, z)
        rotation: Rotation in degrees
        size: Fixture size
        material: Material preset
    """
    fixture_type: str = "ceiling_light"
    position: Tuple[float, float, float] = (0.0, 0.0, 2.8)
    rotation: float = 0.0
    size: float = 0.3
    material: str = "metal_chrome"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "fixture_type": self.fixture_type,
            "position": list(self.position),
            "rotation": self.rotation,
            "size": self.size,
            "material": self.material,
        }


@dataclass
class RoomDetails:
    """
    Complete interior details for a room.

    Attributes:
        room_id: ID of room
        moldings: List of molding configurations
        fixtures: List of fixture configurations
        has_crown_molding: Whether room has crown molding
        has_baseboard: Whether room has baseboard
        has_chair_rail: Whether room has chair rail
        has_wainscoting: Whether room has wainscoting
    """
    room_id: str = ""
    moldings: List[MoldingConfig] = field(default_factory=list)
    fixtures: List[FixtureConfig] = field(default_factory=list)
    has_crown_molding: bool = False
    has_baseboard: bool = True
    has_chair_rail: bool = False
    has_wainscoting: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "room_id": self.room_id,
            "moldings": [m.to_dict() for m in self.moldings],
            "fixtures": [f.to_dict() for f in self.fixtures],
            "has_crown_molding": self.has_crown_molding,
            "has_baseboard": self.has_baseboard,
            "has_chair_rail": self.has_chair_rail,
            "has_wainscoting": self.has_wainscoting,
        }


# Default molding configurations by style
DEFAULT_MOLDING_CONFIGS: Dict[str, Dict[str, MoldingConfig]] = {
    "modern": {
        "baseboard": MoldingConfig(molding_type="baseboard", height=0.08, depth=0.015, style="modern"),
        "crown": MoldingConfig(molding_type="crown", height=0.06, depth=0.06, style="modern"),
    },
    "traditional": {
        "baseboard": MoldingConfig(molding_type="baseboard", height=0.12, depth=0.02, style="colonial"),
        "crown": MoldingConfig(molding_type="crown", height=0.1, depth=0.1, style="colonial"),
        "chair_rail": MoldingConfig(molding_type="chair_rail", height=0.9, depth=0.02, style="colonial"),
    },
    "craftsman": {
        "baseboard": MoldingConfig(molding_type="baseboard", height=0.15, depth=0.02, style="craftsman"),
        "crown": MoldingConfig(molding_type="crown", height=0.08, depth=0.08, style="craftsman"),
        "picture_rail": MoldingConfig(molding_type="picture_rail", height=2.2, depth=0.02, style="craftsman"),
    },
    "victorian": {
        "baseboard": MoldingConfig(molding_type="baseboard", height=0.2, depth=0.025, style="victorian"),
        "crown": MoldingConfig(molding_type="crown", height=0.15, depth=0.15, style="victorian"),
        "chair_rail": MoldingConfig(molding_type="chair_rail", height=1.0, depth=0.03, style="victorian"),
        "picture_rail": MoldingConfig(molding_type="picture_rail", height=2.4, depth=0.02, style="victorian"),
    },
    "minimalist": {
        "baseboard": MoldingConfig(molding_type="baseboard", height=0.05, depth=0.01, style="minimalist"),
    },
    "industrial": {
        "baseboard": MoldingConfig(molding_type="baseboard", height=0.1, depth=0.02, style="industrial"),
    },
}

# Room type to molding requirements
ROOM_MOLDING_REQUIREMENTS: Dict[str, Dict[str, bool]] = {
    "living_room": {"baseboard": True, "crown": True, "chair_rail": False},
    "dining_room": {"baseboard": True, "crown": True, "chair_rail": True},
    "master_bedroom": {"baseboard": True, "crown": True, "chair_rail": False},
    "bedroom": {"baseboard": True, "crown": False, "chair_rail": False},
    "kitchen": {"baseboard": True, "crown": False, "chair_rail": False},
    "bathroom": {"baseboard": True, "crown": False, "chair_rail": False},
    "master_bathroom": {"baseboard": True, "crown": True, "chair_rail": False},
    "office": {"baseboard": True, "crown": True, "chair_rail": False},
    "hallway": {"baseboard": True, "crown": False, "chair_rail": False},
    "foyer": {"baseboard": True, "crown": True, "chair_rail": False},
    "closet": {"baseboard": True, "crown": False, "chair_rail": False},
    "laundry": {"baseboard": True, "crown": False, "chair_rail": False},
}

# Light fixture counts by room type
LIGHT_FIXTURE_REQUIREMENTS: Dict[str, Dict[str, int]] = {
    "living_room": {"ceiling_light": 1, "recessed_light": 4},
    "dining_room": {"ceiling_light": 1},
    "master_bedroom": {"ceiling_light": 1, "wall_sconce": 2},
    "bedroom": {"ceiling_light": 1},
    "kitchen": {"recessed_light": 4},
    "bathroom": {"ceiling_light": 1, "wall_sconce": 2},
    "master_bathroom": {"ceiling_light": 1, "wall_sconce": 4},
    "office": {"ceiling_light": 1},
    "hallway": {"recessed_light": 2},
    "foyer": {"ceiling_light": 1},
    "closet": {"ceiling_light": 1},
    "laundry": {"ceiling_light": 1},
}


class InteriorDetails:
    """
    Interior details generator.

    Creates molding and fixture configurations for rooms.
    """

    def __init__(self, style: str = "modern"):
        """
        Initialize interior details generator.

        Args:
            style: Interior style preset
        """
        self.style = style

    def generate_for_room(self, room: Room) -> RoomDetails:
        """
        Generate interior details for a room.

        Args:
            room: Room to generate details for

        Returns:
            RoomDetails with moldings and fixtures
        """
        details = RoomDetails(room_id=room.id)

        # Get molding configs for style
        style_moldings = DEFAULT_MOLDING_CONFIGS.get(
            self.style,
            DEFAULT_MOLDING_CONFIGS["modern"]
        )

        # Get room requirements
        room_reqs = ROOM_MOLDING_REQUIREMENTS.get(
            room.room_type,
            {"baseboard": True, "crown": False, "chair_rail": False}
        )

        # Add moldings based on requirements
        if room_reqs.get("baseboard", False) and "baseboard" in style_moldings:
            details.moldings.append(style_moldings["baseboard"])
            details.has_baseboard = True

        if room_reqs.get("crown", False) and "crown" in style_moldings:
            details.moldings.append(style_moldings["crown"])
            details.has_crown_molding = True

        if room_reqs.get("chair_rail", False) and "chair_rail" in style_moldings:
            details.moldings.append(style_moldings["chair_rail"])
            details.has_chair_rail = True

        # Generate light fixtures
        light_reqs = LIGHT_FIXTURE_REQUIREMENTS.get(
            room.room_type,
            {"ceiling_light": 1}
        )

        center = room.center
        height = room.height

        # Add ceiling light at center
        if light_reqs.get("ceiling_light", 0) > 0:
            details.fixtures.append(FixtureConfig(
                fixture_type="ceiling_light",
                position=(center[0], center[1], height),
                size=0.4,
            ))

        # Add recessed lights
        recessed_count = light_reqs.get("recessed_light", 0)
        if recessed_count > 0:
            bounds = room.bounds
            details.fixtures.extend(
                self._generate_recessed_lights(
                    bounds, height, recessed_count
                )
            )

        # Add wall sconces
        sconce_count = light_reqs.get("wall_sconce", 0)
        if sconce_count > 0:
            details.fixtures.extend(
                self._generate_wall_sconces(room, sconce_count)
            )

        return details

    def _generate_recessed_lights(
        self,
        bounds: Tuple[float, float, float, float],
        height: float,
        count: int
    ) -> List[FixtureConfig]:
        """Generate recessed light positions."""
        fixtures = []

        min_x, min_y, max_x, max_y = bounds
        width = max_x - min_x
        depth = max_y - min_y

        # Create grid pattern
        cols = int(count ** 0.5) + 1
        rows = (count + cols - 1) // cols

        spacing_x = width / (cols + 1)
        spacing_y = depth / (rows + 1)

        for row in range(rows):
            for col in range(cols):
                if len(fixtures) >= count:
                    break

                x = min_x + spacing_x * (col + 1)
                y = min_y + spacing_y * (row + 1)

                fixtures.append(FixtureConfig(
                    fixture_type="recessed_light",
                    position=(x, y, height),
                    size=0.15,
                ))

        return fixtures

    def _generate_wall_sconces(
        self,
        room: Room,
        count: int
    ) -> List[FixtureConfig]:
        """Generate wall sconce positions."""
        fixtures = []
        center = room.center
        height = room.height

        # Place sconces on opposite walls
        bounds = room.bounds
        sconce_height = 1.8  # Standard sconce height

        if count >= 2:
            # Two sconces on opposite walls
            fixtures.append(FixtureConfig(
                fixture_type="wall_sconce",
                position=(bounds[0] + 0.1, center[1], sconce_height),
                rotation=90.0,
                size=0.15,
            ))
            fixtures.append(FixtureConfig(
                fixture_type="wall_sconce",
                position=(bounds[2] - 0.1, center[1], sconce_height),
                rotation=-90.0,
                size=0.15,
            ))

        if count >= 4:
            # Four sconces on all walls
            fixtures.append(FixtureConfig(
                fixture_type="wall_sconce",
                position=(center[0], bounds[1] + 0.1, sconce_height),
                rotation=0.0,
                size=0.15,
            ))
            fixtures.append(FixtureConfig(
                fixture_type="wall_sconce",
                position=(center[0], bounds[3] - 0.1, sconce_height),
                rotation=180.0,
                size=0.15,
            ))

        return fixtures


def add_interior_details(
    plan: FloorPlan,
    style: Optional[str] = None
) -> List[RoomDetails]:
    """
    Add interior details to all rooms in a floor plan.

    Args:
        plan: FloorPlan to process
        style: Optional style override (uses plan.style if not provided)

    Returns:
        List of RoomDetails for each room
    """
    details_generator = InteriorDetails(style=style or plan.style)

    all_details = []
    for room in plan.rooms:
        details = details_generator.generate_for_room(room)
        all_details.append(details)

    return all_details


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "MoldingType",
    "FixtureType",
    "MoldingConfig",
    "FixtureConfig",
    "RoomDetails",
    "InteriorDetails",
    "DEFAULT_MOLDING_CONFIGS",
    "ROOM_MOLDING_REQUIREMENTS",
    "LIGHT_FIXTURE_REQUIREMENTS",
    "add_interior_details",
]
