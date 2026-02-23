"""
Floor Plan Generator

High-level floor plan generation with presets for different building types.
Provides convenient factory functions for common floor plan configurations.

Implements REQ-IL-01: Floor Plan Generator convenience functions.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import random

from .types import (
    FloorPlan,
    Room,
    RoomType,
    InteriorStyle,
)
from .bsp_solver import BSPSolver, generate_floor_plan


# =============================================================================
# FLOOR PLAN PRESETS
# =============================================================================

@dataclass
class FloorPlanPreset:
    """Floor plan preset configuration."""
    name: str
    description: str
    width: float
    height: float
    room_count: int
    room_types: List[str]
    style: str
    seed: Optional[int] = None


# Predefined floor plan presets
FLOOR_PLAN_PRESETS: Dict[str, FloorPlanPreset] = {
    # Apartments
    "studio_apartment": FloorPlanPreset(
        name="Studio Apartment",
        description="Open plan studio with sleeping/living combo",
        width=6.0,
        height=8.0,
        room_count=3,
        room_types=["living_room", "kitchen", "bathroom"],
        style="modern",
    ),
    "one_bedroom_apartment": FloorPlanPreset(
        name="One Bedroom Apartment",
        description="Standard one bedroom apartment",
        width=8.0,
        height=10.0,
        room_count=5,
        room_types=["living_room", "kitchen", "bedroom", "bathroom", "closet"],
        style="modern",
    ),
    "two_bedroom_apartment": FloorPlanPreset(
        name="Two Bedroom Apartment",
        description="Two bedroom apartment with master suite",
        width=10.0,
        height=12.0,
        room_count=7,
        room_types=["living_room", "kitchen", "master_bedroom", "bedroom",
                   "master_bathroom", "bathroom", "laundry"],
        style="contemporary",
    ),
    "luxury_apartment": FloorPlanPreset(
        name="Luxury Apartment",
        description="Spacious luxury apartment with multiple rooms",
        width=14.0,
        height=12.0,
        room_count=9,
        room_types=["living_room", "dining_room", "kitchen", "master_bedroom",
                   "bedroom", "master_bathroom", "bathroom", "office", "laundry"],
        style="contemporary",
    ),

    # Houses
    "small_house": FloorPlanPreset(
        name="Small House",
        description="Compact single-story house",
        width=10.0,
        height=8.0,
        room_count=5,
        room_types=["living_room", "kitchen", "bedroom", "bathroom", "laundry"],
        style="traditional",
    ),
    "medium_house": FloorPlanPreset(
        name="Medium House",
        description="Medium-sized family home",
        width=12.0,
        height=10.0,
        room_count=7,
        room_types=["living_room", "dining_room", "kitchen", "master_bedroom",
                   "bedroom", "bathroom", "laundry"],
        style="modern",
    ),
    "large_house": FloorPlanPreset(
        name="Large House",
        description="Spacious family home with many rooms",
        width=16.0,
        height=12.0,
        room_count=10,
        room_types=["living_room", "family_room", "dining_room", "kitchen",
                   "master_bedroom", "bedroom", "bedroom", "master_bathroom",
                   "bathroom", "office"],
        style="modern",
    ),
    "mansion": FloorPlanPreset(
        name="Mansion",
        description="Large luxury home with all amenities",
        width=20.0,
        height=16.0,
        room_count=14,
        room_types=["living_room", "family_room", "dining_room", "kitchen",
                   "master_bedroom", "bedroom", "bedroom", "bedroom",
                   "master_bathroom", "bathroom", "bathroom", "office",
                   "library", "laundry"],
        style="traditional",
    ),

    # Offices
    "small_office": FloorPlanPreset(
        name="Small Office",
        description="Compact office space",
        width=8.0,
        height=6.0,
        room_count=3,
        room_types=["office", "office", "bathroom"],
        style="industrial",
    ),
    "medium_office": FloorPlanPreset(
        name="Medium Office",
        description="Standard office floor plan",
        width=12.0,
        height=10.0,
        room_count=6,
        room_types=["office", "office", "office", "office", "bathroom", "storage"],
        style="modern",
    ),
    "large_office": FloorPlanPreset(
        name="Large Office",
        description="Open plan office with meeting rooms",
        width=16.0,
        height=12.0,
        room_count=8,
        room_types=["office", "office", "office", "office", "office",
                   "office", "bathroom", "storage"],
        style="contemporary",
    ),

    # Specialty
    "loft": FloorPlanPreset(
        name="Loft",
        description="Industrial loft conversion",
        width=12.0,
        height=10.0,
        room_count=4,
        room_types=["living_room", "kitchen", "bedroom", "bathroom"],
        style="industrial",
    ),
    "cottage": FloorPlanPreset(
        name="Cottage",
        description="Cozy cottage floor plan",
        width=8.0,
        height=7.0,
        room_count=4,
        room_types=["living_room", "kitchen", "bedroom", "bathroom"],
        style="rustic",
    ),
    "penthouse": FloorPlanPreset(
        name="Penthouse",
        description="Luxury penthouse apartment",
        width=14.0,
        height=14.0,
        room_count=8,
        room_types=["living_room", "dining_room", "kitchen", "master_bedroom",
                   "bedroom", "master_bathroom", "office", "laundry"],
        style="contemporary",
    ),
}


class FloorPlanGenerator:
    """
    High-level floor plan generator with presets and customization.

    Provides convenient methods for generating various types of floor plans
    with sensible defaults for different building types and styles.

    Usage:
        generator = FloorPlanGenerator()
        plan = generator.generate_preset("two_bedroom_apartment")
        plan = generator.generate_custom(width=10, height=8, room_count=5)
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize floor plan generator.

        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed

    def generate_preset(self, preset_name: str) -> FloorPlan:
        """
        Generate floor plan from preset.

        Args:
            preset_name: Name of preset to use

        Returns:
            Generated FloorPlan

        Raises:
            ValueError: If preset name not found
        """
        if preset_name not in FLOOR_PLAN_PRESETS:
            available = list(FLOOR_PLAN_PRESETS.keys())
            raise ValueError(f"Unknown preset '{preset_name}'. Available: {available}")

        preset = FLOOR_PLAN_PRESETS[preset_name]

        solver = BSPSolver(
            seed=preset.seed or self.seed,
            style=preset.style,
        )

        return solver.generate(
            width=preset.width,
            height=preset.height,
            room_count=preset.room_count,
            room_types=preset.room_types,
        )

    def generate_custom(
        self,
        width: float,
        height: float,
        room_count: int,
        room_types: Optional[List[str]] = None,
        style: str = "modern",
        seed: Optional[int] = None,
    ) -> FloorPlan:
        """
        Generate custom floor plan.

        Args:
            width: Floor plan width in meters
            height: Floor plan height in meters
            room_count: Number of rooms
            room_types: Optional list of room types
            style: Interior style preset
            seed: Random seed (overrides instance seed)

        Returns:
            Generated FloorPlan
        """
        solver = BSPSolver(
            seed=seed or self.seed,
            style=style,
        )

        return solver.generate(
            width=width,
            height=height,
            room_count=room_count,
            room_types=room_types,
        )

    def list_presets(self) -> List[str]:
        """Get list of available preset names."""
        return list(FLOOR_PLAN_PRESETS.keys())

    def get_preset_info(self, preset_name: str) -> Dict[str, Any]:
        """Get information about a preset."""
        if preset_name not in FLOOR_PLAN_PRESETS:
            raise ValueError(f"Unknown preset '{preset_name}'")

        preset = FLOOR_PLAN_PRESETS[preset_name]
        return {
            "name": preset.name,
            "description": preset.description,
            "dimensions": (preset.width, preset.height),
            "area": preset.width * preset.height,
            "room_count": preset.room_count,
            "room_types": preset.room_types,
            "style": preset.style,
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def generate_apartment_floor_plan(
    size: str = "medium",
    seed: Optional[int] = None,
) -> FloorPlan:
    """
    Generate apartment floor plan.

    Args:
        size: Size preset ("studio", "one_bedroom", "two_bedroom", "luxury")
        seed: Random seed for reproducibility

    Returns:
        Generated FloorPlan
    """
    preset_map = {
        "studio": "studio_apartment",
        "one_bedroom": "one_bedroom_apartment",
        "two_bedroom": "two_bedroom_apartment",
        "luxury": "luxury_apartment",
        "medium": "one_bedroom_apartment",  # Default
    }

    preset_name = preset_map.get(size, "one_bedroom_apartment")
    generator = FloorPlanGenerator(seed=seed)
    return generator.generate_preset(preset_name)


def generate_office_floor_plan(
    size: str = "medium",
    seed: Optional[int] = None,
) -> FloorPlan:
    """
    Generate office floor plan.

    Args:
        size: Size preset ("small", "medium", "large")
        seed: Random seed for reproducibility

    Returns:
        Generated FloorPlan
    """
    preset_map = {
        "small": "small_office",
        "medium": "medium_office",
        "large": "large_office",
    }

    preset_name = preset_map.get(size, "medium_office")
    generator = FloorPlanGenerator(seed=seed)
    return generator.generate_preset(preset_name)


def generate_house_floor_plan(
    size: str = "medium",
    seed: Optional[int] = None,
) -> FloorPlan:
    """
    Generate house floor plan.

    Args:
        size: Size preset ("small", "medium", "large", "mansion")
        seed: Random seed for reproducibility

    Returns:
        Generated FloorPlan
    """
    preset_map = {
        "small": "small_house",
        "medium": "medium_house",
        "large": "large_house",
        "mansion": "mansion",
    }

    preset_name = preset_map.get(size, "medium_house")
    generator = FloorPlanGenerator(seed=seed)
    return generator.generate_preset(preset_name)


def list_floor_plan_presets() -> List[str]:
    """Get list of all available floor plan presets."""
    return list(FLOOR_PLAN_PRESETS.keys())


def get_floor_plan_preset(preset_name: str) -> FloorPlanPreset:
    """Get floor plan preset configuration."""
    if preset_name not in FLOOR_PLAN_PRESETS:
        raise ValueError(f"Unknown preset '{preset_name}'")
    return FLOOR_PLAN_PRESETS[preset_name]


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "FloorPlanPreset",
    "FLOOR_PLAN_PRESETS",
    "FloorPlanGenerator",
    "generate_apartment_floor_plan",
    "generate_office_floor_plan",
    "generate_house_floor_plan",
    "list_floor_plan_presets",
    "get_floor_plan_preset",
]
