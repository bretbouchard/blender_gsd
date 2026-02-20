"""
Car Styling System - Node-Based Style Control

Provides a clean interface for controlling car appearance through
Geometry Nodes inputs and material parameters.

The system exposes:
- Body style (proportions, parts selection)
- Color scheme (body, glass, trim, wheels)
- Detail level (low-poly to high-detail)
- Weathering/damage state

Usage:
    from lib.animation.vehicle.car_styling import CarStyler

    styler = CarStyler(car_object)
    styler.set_body_color((0.8, 0.1, 0.1))  # Red
    styler.set_style("sports")
    styler.randomize_variations(seed=42)
"""

import bpy
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from mathutils import Vector, Color
import math


@dataclass
class BodyProportions:
    """Proportional controls for car body."""
    length: float = 1.0      # Multiplier for length
    width: float = 1.0       # Multiplier for width
    height: float = 1.0      # Multiplier for height
    wheel_size: float = 1.0  # Wheel radius multiplier
    ground_clearance: float = 1.0  # Ride height multiplier
    wheelbase_ratio: float = 0.6  # Wheelbase as fraction of length
    track_width_ratio: float = 0.8  # Track as fraction of width


@dataclass
class ColorScheme:
    """Complete color scheme for a car."""
    primary: Tuple[float, float, float] = (0.5, 0.5, 0.5)
    secondary: Tuple[float, float, float] = (0.3, 0.3, 0.3)  # Roof, trim
    accent: Tuple[float, float, float] = (0.8, 0.8, 0.8)  # Chrome, details
    glass: Tuple[float, float, float, float] = (0.2, 0.3, 0.4, 0.5)
    wheel: Tuple[float, float, float] = (0.2, 0.2, 0.2)
    tire: Tuple[float, float, float] = (0.05, 0.05, 0.05)
    headlight: Tuple[float, float, float] = (1.0, 1.0, 0.9)
    taillight: Tuple[float, float, float] = (1.0, 0.2, 0.1)
    metalness: float = 0.8
    roughness: float = 0.3


@dataclass
class PartSelection:
    """Part variant selection for each component."""
    front_base: int = 1      # 1-14
    back_base: int = 1       # 1-13
    front_bumper: int = 1    # 1-10
    back_bumper: int = 1     # 1-9
    front_headlights: int = 1  # 1-11
    back_headlights: int = 1   # 1-13
    wheel_style: int = 1     # 1-11
    mirror_style: int = 1    # 1-5
    handle_style: int = 1    # 1-5
    grill_style: int = 1     # 1-8


@dataclass
class DetailLevel:
    """Detail/complexity settings."""
    subdivision: int = 0     # Subdivision levels (0-2)
    bevel_amount: float = 0.0  # Edge bevel (0-1)
    panel_lines: bool = False  # Add panel line details
    door_handles: bool = True
    mirrors: bool = True
    antenna: bool = False
    exhaust: bool = True


@dataclass
class Weathering:
    """Weathering/damage state."""
    dirt_amount: float = 0.0    # 0-1
    dust_color: Tuple[float, float, float] = (0.4, 0.35, 0.3)
    scratches: float = 0.0      # 0-1
    dents: float = 0.0          # 0-1
    rust: float = 0.0           # 0-1
    rust_color: Tuple[float, float, float] = (0.4, 0.2, 0.1)


# Predefined style configurations
STYLE_CONFIGS = {
    "economy": {
        "proportions": BodyProportions(length=0.9, width=0.9, height=0.95),
        "parts": PartSelection(front_base=1, back_base=1, wheel_style=1),
        "detail": DetailLevel(subdivision=0, mirrors=False),
    },
    "sedan": {
        "proportions": BodyProportions(length=1.0, width=1.0, height=1.0),
        "parts": PartSelection(front_base=3, back_base=3, wheel_style=3),
        "detail": DetailLevel(subdivision=0),
    },
    "sports": {
        "proportions": BodyProportions(length=1.1, width=1.05, height=0.85, ground_clearance=0.8),
        "parts": PartSelection(front_base=5, back_base=5, wheel_style=6),
        "detail": DetailLevel(subdivision=1, panel_lines=True),
    },
    "suv": {
        "proportions": BodyProportions(length=1.1, width=1.1, height=1.2, ground_clearance=1.3),
        "parts": PartSelection(front_base=8, back_base=8, wheel_style=8),
        "detail": DetailLevel(subdivision=0),
    },
    "pickup": {
        "proportions": BodyProportions(length=1.3, width=1.1, height=1.1, wheelbase_ratio=0.7),
        "parts": PartSelection(front_base=10, back_base=1, wheel_style=10),
        "detail": DetailLevel(subdivision=0),
    },
    "luxury": {
        "proportions": BodyProportions(length=1.15, width=1.05, height=1.0),
        "parts": PartSelection(front_base=12, back_base=12, wheel_style=9),
        "detail": DetailLevel(subdivision=1, panel_lines=True, antenna=True),
    },
    "muscle": {
        "proportions": BodyProportions(length=1.1, width=1.05, height=0.9, wheel_size=1.1),
        "parts": PartSelection(front_base=2, back_base=3, wheel_style=5),
        "detail": DetailLevel(subdivision=0, exhaust=True),
    },
    "compact": {
        "proportions": BodyProportions(length=0.85, width=0.9, height=1.0),
        "parts": PartSelection(front_base=4, back_base=4, wheel_style=2),
        "detail": DetailLevel(subdivision=0, mirrors=True),
    },
}

# Color scheme presets
COLOR_SCHEMES = {
    "cherry_red": ColorScheme(
        primary=(0.85, 0.1, 0.1),
        secondary=(0.1, 0.1, 0.1),
        metalness=0.9, roughness=0.2
    ),
    "racing_red": ColorScheme(
        primary=(0.9, 0.0, 0.0),
        secondary=(0.1, 0.1, 0.1),
        accent=(1.0, 1.0, 1.0),  # White accents
        metalness=0.95, roughness=0.15
    ),
    "midnight_blue": ColorScheme(
        primary=(0.1, 0.15, 0.35),
        secondary=(0.05, 0.05, 0.1),
        metalness=0.85, roughness=0.25
    ),
    "forest_green": ColorScheme(
        primary=(0.1, 0.35, 0.15),
        secondary=(0.05, 0.1, 0.05),
        metalness=0.8, roughness=0.3
    ),
    "canary_yellow": ColorScheme(
        primary=(0.95, 0.85, 0.1),
        secondary=(0.1, 0.1, 0.1),
        metalness=0.85, roughness=0.2
    ),
    "pearl_white": ColorScheme(
        primary=(0.95, 0.95, 0.97),
        secondary=(0.2, 0.2, 0.2),
        metalness=0.7, roughness=0.15
    ),
    "obsidian_black": ColorScheme(
        primary=(0.02, 0.02, 0.02),
        secondary=(0.1, 0.1, 0.1),
        accent=(0.3, 0.3, 0.3),
        metalness=0.95, roughness=0.1
    ),
    "silver_metallic": ColorScheme(
        primary=(0.7, 0.7, 0.75),
        secondary=(0.2, 0.2, 0.2),
        metalness=0.9, roughness=0.2
    ),
    "sunset_orange": ColorScheme(
        primary=(1.0, 0.4, 0.0),
        secondary=(0.1, 0.1, 0.1),
        metalness=0.85, roughness=0.2
    ),
    "electric_purple": ColorScheme(
        primary=(0.5, 0.1, 0.8),
        secondary=(0.1, 0.1, 0.1),
        metalness=0.9, roughness=0.15
    ),
    "matte_gray": ColorScheme(
        primary=(0.4, 0.4, 0.4),
        secondary=(0.2, 0.2, 0.2),
        metalness=0.1, roughness=0.8
    ),
    "police": ColorScheme(
        primary=(0.1, 0.1, 0.4),
        secondary=(0.9, 0.9, 0.9),  # White
        accent=(0.0, 0.3, 0.8),  # Blue stripe
        metalness=0.7, roughness=0.3
    ),
    "taxi": ColorScheme(
        primary=(0.95, 0.8, 0.0),
        secondary=(0.1, 0.1, 0.1),
        metalness=0.6, roughness=0.4
    ),
}


class CarStyler:
    """
    High-level interface for styling procedural cars.

    This class provides methods to modify car appearance
    without dealing directly with Geometry Nodes or materials.
    """

    def __init__(self, car_object: bpy.types.Object):
        self.car = car_object
        self._geo_modifier = None
        self._materials: Dict[str, bpy.types.Material] = {}

        # Find geometry nodes modifier
        for mod in car_object.modifiers:
            if mod.type == 'NODES':
                self._geo_modifier = mod
                break

    def set_style(self, style_name: str) -> None:
        """Apply a predefined style configuration."""
        if style_name not in STYLE_CONFIGS:
            raise ValueError(f"Unknown style: {style_name}. Available: {list(STYLE_CONFIGS.keys())}")

        config = STYLE_CONFIGS[style_name]

        # Apply proportions
        if "proportions" in config:
            self.apply_proportions(config["proportions"])

        # Apply part selection
        if "parts" in config:
            self.apply_parts(config["parts"])

        # Apply detail level
        if "detail" in config:
            self.apply_detail(config["detail"])

    def set_color_scheme(self, scheme_name: str) -> None:
        """Apply a predefined color scheme."""
        if scheme_name not in COLOR_SCHEMES:
            raise ValueError(f"Unknown color scheme: {scheme_name}. Available: {list(COLOR_SCHEMES.keys())}")

        self.apply_color_scheme(COLOR_SCHEMES[scheme_name])

    def set_body_color(self, color: Tuple[float, float, float]) -> None:
        """Set the primary body color."""
        mat = self._get_body_material()
        if mat and mat.use_nodes:
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                bsdf.inputs["Base Color"].default_value = (*color, 1.0)

    def apply_proportions(self, proportions: BodyProportions) -> None:
        """Apply body proportion multipliers."""
        if not self._geo_modifier or not self._geo_modifier.node_group:
            return

        # Scale the car object
        self.car.scale = (
            proportions.width,
            proportions.length,
            proportions.height
        )

    def apply_parts(self, parts: PartSelection) -> None:
        """Apply part variant selection."""
        if not self._geo_modifier:
            return

        # These would need to be exposed as inputs on the node group
        # For now, store as custom properties
        self.car["parts_front_base"] = parts.front_base
        self.car["parts_back_base"] = parts.back_base
        self.car["parts_front_bumper"] = parts.front_bumper
        self.car["parts_back_bumper"] = parts.back_bumper
        self.car["parts_front_lights"] = parts.front_headlights
        self.car["parts_back_lights"] = parts.back_headlights
        self.car["parts_wheel_style"] = parts.wheel_style

    def apply_detail(self, detail: DetailLevel) -> None:
        """Apply detail level settings."""
        # Add subdivision modifier if needed
        if detail.subdivision > 0:
            sub_mod = self.car.modifiers.get("Subdivision")
            if not sub_mod:
                sub_mod = self.car.modifiers.new("Subdivision", 'SUBSURF')
            sub_mod.levels = detail.subdivision

    def apply_color_scheme(self, scheme: ColorScheme) -> None:
        """Apply a complete color scheme."""
        # Body material
        body_mat = self._get_or_create_material("Body")
        self._apply_color_to_material(body_mat, scheme.primary, scheme.metalness, scheme.roughness)

        # Glass material
        glass_mat = self._get_or_create_material("Glass")
        if glass_mat and glass_mat.use_nodes:
            bsdf = glass_mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                bsdf.inputs["Base Color"].default_value = scheme.glass
                bsdf.inputs["Roughness"].default_value = 0.0
                bsdf.inputs["Transmission"].default_value = 0.9

        # Chrome/metal material
        chrome_mat = self._get_or_create_material("Chrome")
        if chrome_mat and chrome_mat.use_nodes:
            bsdf = chrome_mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                bsdf.inputs["Base Color"].default_value = (*scheme.accent, 1.0)
                bsdf.inputs["Metallic"].default_value = 1.0
                bsdf.inputs["Roughness"].default_value = 0.1

    def apply_weathering(self, weathering: Weathering) -> None:
        """Apply weathering/damage effects."""
        # Store weathering data for shader access
        self.car["weathering_dirt"] = weathering.dirt_amount
        self.car["weathering_scratches"] = weathering.scratches
        self.car["weathering_dents"] = weathering.dents
        self.car["weathering_rust"] = weathering.rust

    def randomize_variations(self, seed: int = 0) -> None:
        """Randomize part variations with a seed."""
        import random
        random.seed(seed)

        parts = PartSelection(
            front_base=random.randint(1, 14),
            back_base=random.randint(1, 13),
            front_bumper=random.randint(1, 10),
            back_bumper=random.randint(1, 9),
            front_headlights=random.randint(1, 11),
            back_headlights=random.randint(1, 13),
            wheel_style=random.randint(1, 11),
            mirror_style=random.randint(1, 5),
            handle_style=random.randint(1, 5),
        )
        self.apply_parts(parts)

    def _get_body_material(self) -> Optional[bpy.types.Material]:
        """Get the body material from car object."""
        if self.car.data.materials:
            return self.car.data.materials[0]
        return None

    def _get_or_create_material(self, name: str) -> bpy.types.Material:
        """Get or create a material by name."""
        full_name = f"{self.car.name}_{name}"

        if full_name in bpy.data.materials:
            return bpy.data.materials[full_name]

        mat = bpy.data.materials.new(name=full_name)
        mat.use_nodes = True
        return mat

    def _apply_color_to_material(
        self,
        mat: bpy.types.Material,
        color: Tuple[float, float, float],
        metalness: float = 0.8,
        roughness: float = 0.3
    ) -> None:
        """Apply color settings to a Principled BSDF material."""
        if not mat or not mat.use_nodes:
            return

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*color, 1.0)
            bsdf.inputs["Metallic"].default_value = metalness
            bsdf.inputs["Roughness"].default_value = roughness


def style_car(
    car_object: bpy.types.Object,
    style: str = "sedan",
    color_scheme: str = "cherry_red",
    seed: Optional[int] = None
) -> CarStyler:
    """
    Convenience function to quickly style a car.

    Args:
        car_object: The car object to style
        style: Style preset name
        color_scheme: Color scheme preset name
        seed: Optional seed for randomization

    Returns:
        CarStyler instance for further modifications
    """
    styler = CarStyler(car_object)
    styler.set_style(style)
    styler.set_color_scheme(color_scheme)

    if seed is not None:
        styler.randomize_variations(seed)

    return styler
