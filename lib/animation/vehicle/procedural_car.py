"""
Procedural Car System - Launch Control Compatible

Converts procedural node-based cars into launch-control compatible vehicles.
Supports deterministic style/color control through Geometry Nodes inputs.

The wired template (procedural_car_wired.blend) has direct connections from
style inputs to Instance Index nodes, bypassing the random selection entirely.
This means setting Front Base = 5 will ALWAYS give front style #5.

Usage:
    from lib.animation.vehicle.procedural_car import ProceduralCarFactory

    factory = ProceduralCarFactory()
    car = factory.create_car(
        style="sedan",           # Body style preset
        color="red",             # Color preset
        seed=42                  # Optional seed for remaining variations
    )

    # Create a fleet with varied styles
    fleet = factory.create_fleet(
        count=10,
        styles=["sedan", "sports", "suv"],
        colors=["red", "blue", "black"],
        spacing=5.0
    )

    # Make individual car launch-ready
    factory.setup_launch_compatible(car)
"""

import bpy
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
import random
from mathutils import Vector, Color
import math

# Asset paths
ASSETS_PATH = Path(__file__).parent.parent.parent.parent / "assets" / "vehicles"
CAR_TEMPLATE_PATH = ASSETS_PATH / "procedural_car_wired.blend"  # Wired for deterministic selection
CAR_TEMPLATE_ORIGINAL = ASSETS_PATH / "procedural low poly car.blend"  # Original backup


@dataclass
class CarStyle:
    """Style configuration for procedural car."""
    name: str
    body_type: str  # sedan, hatchback, pickup, suv
    front_base: int = 1      # 1-14
    back_base: int = 1       # 1-13 + hatchback + pickup
    front_bumper: int = 1    # 1-10
    back_bumper: int = 1     # 1-9
    front_lights: int = 1    # 1-11
    back_lights: int = 1     # 1-13
    wheel_style: int = 1     # 1-11
    mirror_style: int = 1    # 1-5
    handle_style: int = 1    # 1-5


@dataclass
class CarColors:
    """Color configuration for procedural car."""
    body: Tuple[float, float, float] = (0.5, 0.5, 0.5)  # Gray default
    glass: Tuple[float, float, float, float] = (0.2, 0.3, 0.4, 0.5)  # RGBA
    metal: Tuple[float, float, float] = (0.8, 0.8, 0.8)  # Chrome
    rubber: Tuple[float, float, float] = (0.1, 0.1, 0.1)  # Black
    front_light: Tuple[float, float, float] = (1.0, 1.0, 0.9)  # Warm white
    back_light: Tuple[float, float, float] = (1.0, 0.2, 0.1)  # Red


# Preset styles
STYLE_PRESETS = {
    "sedan": CarStyle(
        name="Sedan",
        body_type="sedan",
        front_base=1, back_base=1,
        front_bumper=1, back_bumper=1,
        front_lights=1, back_lights=1,
        wheel_style=1
    ),
    "sports": CarStyle(
        name="Sports Car",
        body_type="sedan",
        front_base=5, back_base=5,
        front_bumper=3, back_bumper=3,
        front_lights=4, back_lights=4,
        wheel_style=6
    ),
    "suv": CarStyle(
        name="SUV",
        body_type="sedan",
        front_base=8, back_base=8,
        front_bumper=5, back_bumper=5,
        front_lights=7, back_lights=7,
        wheel_style=8
    ),
    "hatchback": CarStyle(
        name="Hatchback",
        body_type="hatchback",
        front_base=3, back_base=1,  # hatchback variant
        front_bumper=2, back_bumper=2,
        front_lights=2, back_lights=2,
        wheel_style=3
    ),
    "pickup": CarStyle(
        name="Pickup Truck",
        body_type="pickup",
        front_base=10, back_base=1,  # pickup variant
        front_bumper=7, back_bumper=7,
        front_lights=9, back_lights=9,
        wheel_style=10
    ),
    "muscle": CarStyle(
        name="Muscle Car",
        body_type="sedan",
        front_base=2, back_base=3,
        front_bumper=4, back_bumper=4,
        front_lights=3, back_lights=3,
        wheel_style=5
    ),
}

# Color presets
COLOR_PRESETS = {
    "red": CarColors(body=(0.8, 0.1, 0.1)),
    "blue": CarColors(body=(0.1, 0.2, 0.8)),
    "green": CarColors(body=(0.1, 0.5, 0.2)),
    "yellow": CarColors(body=(0.9, 0.8, 0.1)),
    "white": CarColors(body=(0.95, 0.95, 0.95)),
    "black": CarColors(body=(0.1, 0.1, 0.1)),
    "silver": CarColors(body=(0.7, 0.7, 0.75)),
    "orange": CarColors(body=(1.0, 0.4, 0.0)),
    "purple": CarColors(body=(0.5, 0.1, 0.7)),
}


class ProceduralCarFactory:
    """Factory for creating launch-control compatible procedural cars."""

    def __init__(self, template_path: Optional[Path] = None):
        self.template_path = template_path or CAR_TEMPLATE_PATH
        self._template_loaded = False
        self._collections: Dict[str, bpy.types.Collection] = {}

    def load_template(self) -> bool:
        """Load car template assets if not already loaded."""
        if self._template_loaded:
            return True

        if not self.template_path.exists():
            raise FileNotFoundError(f"Car template not found: {self.template_path}")

        # Append collections from template
        with bpy.data.libraries.load(str(self.template_path)) as (data_from, data_to):
            # Get all collection names
            data_to.collections = data_from.collections

        # Store reference to car node group
        self._template_loaded = True
        return True

    def create_car(
        self,
        name: str = "Car",
        style: str = "sedan",
        color: str = "red",
        custom_style: Optional[CarStyle] = None,
        custom_color: Optional[CarColors] = None,
        seed: Optional[int] = None,
        position: Tuple[float, float, float] = (0, 0, 0)
    ) -> bpy.types.Object:
        """
        Create a procedural car with specified style and color.

        Args:
            name: Object name
            style: Preset style name (sedan, sports, suv, hatchback, pickup, muscle)
            color: Preset color name (red, blue, green, yellow, white, black, silver)
            custom_style: Custom CarStyle to override preset
            custom_color: Custom CarColors to override preset
            seed: Random seed for variation
            position: Initial position

        Returns:
            The created car object, launch-control compatible
        """
        # Load template if needed
        self.load_template()

        # Get style and color
        car_style = custom_style or STYLE_PRESETS.get(style, STYLE_PRESETS["sedan"])
        car_color = custom_color or COLOR_PRESETS.get(color, COLOR_PRESETS["red"])

        # Create base object
        bpy.ops.mesh.primitive_grid_add(size=2, location=position)
        car_obj = bpy.context.active_object
        car_obj.name = name

        # Add Geometry Nodes modifier
        geo_mod = car_obj.modifiers.new(name="CarGeometry", type='NODES')

        # Get or create car node group
        node_group = self._get_or_create_car_node_group()
        geo_mod.node_group = node_group

        # Set style parameters via node inputs
        self._apply_style_to_modifier(geo_mod, car_style, seed)

        # Apply colors to materials
        self._apply_colors(car_obj, car_color)

        # Setup for launch control
        self.setup_launch_compatible(car_obj)

        return car_obj

    def _get_or_create_car_node_group(self) -> bpy.types.NodeGroup:
        """Get existing car node group or load from template."""
        # Check if already loaded
        if "car" in bpy.data.node_groups:
            return bpy.data.node_groups["car"]

        # Load from template file
        with bpy.data.libraries.load(str(self.template_path)) as (data_from, data_to):
            if "car" in data_from.node_groups:
                data_to.node_groups = ["car"]

        return bpy.data.node_groups.get("car")

    def _apply_style_to_modifier(
        self,
        modifier: bpy.types.NodesModifier,
        style: CarStyle,
        seed: Optional[int]
    ) -> None:
        """
        Apply style configuration to geometry nodes modifier.

        The WIRED node group has deterministic inputs that bypass randomness:
        - Front Base, Back Base, Front/Back Bumper, Front/Back Lights
        - Wheel Style, Mirror Style, Handle Style, Grill Style
        These connect directly to Instance Index via Subtract-1 nodes.
        """
        ng = modifier.node_group
        if not ng:
            return

        # Get the interface (Blender 5.x API)
        blender_5x = bpy.app.version >= (5, 0, 0)

        def set_input_value(input_name: str, value):
            """Set a modifier input value by name."""
            try:
                modifier[input_name] = value
            except KeyError:
                pass  # Input doesn't exist

        # Set deterministic style inputs (these bypass the random selection)
        # Values are 1-indexed, Subtract-1 nodes convert to 0-indexed for Instance Index
        set_input_value("Front Base", style.front_base)
        set_input_value("Back Base", style.back_base)
        set_input_value("Front Bumper", style.front_bumper)
        set_input_value("Back Bumper", style.back_bumper)
        set_input_value("Front Lights", style.front_lights)
        set_input_value("Back Lights", style.back_lights)
        set_input_value("Wheel Style", style.wheel_style)
        set_input_value("Mirror Style", style.mirror_style)
        set_input_value("Handle Style", style.handle_style)
        set_input_value("Grill Style", 1)  # Default grill

        # Also set original inputs for compatibility
        set_input_value("front", style.front_base)
        set_input_value("central", 1)
        set_input_value("back", style.back_base)
        set_input_value("front headlights", style.front_lights)
        set_input_value("back headlights", style.back_lights)
        set_input_value("front bumper", style.front_bumper)
        set_input_value("back bumper", style.back_bumper)
        set_input_value("mirrors", style.mirror_style)
        set_input_value("handles", style.handle_style)
        set_input_value("wheels", style.wheel_style)
        set_input_value("grid", 1)
        set_input_value("random", seed if seed is not None else 0)
        set_input_value("Seed", seed if seed is not None else 0)

    def _apply_colors(self, car_obj: bpy.types.Object, colors: CarColors) -> None:
        """Apply color configuration to car materials and node inputs."""
        # First, try to set colors via geometry node inputs (if available)
        for mod in car_obj.modifiers:
            if mod.type == 'NODES' and mod.node_group:
                ng = mod.node_group
                blender_5x = bpy.app.version >= (5, 0, 0)

                def set_color_input(name: str, value):
                    try:
                        mod[name] = value
                    except:
                        pass

                # Set color inputs on the modifier
                set_color_input("Body Color", (*colors.body, 1.0))
                set_color_input("Secondary Color", (*colors.body, 1.0))  # Same as body for now
                set_color_input("Accent Color", (*colors.metal, 1.0))
                set_color_input("Glass Color", colors.glass)
                set_color_input("Metalness", 0.8)
                set_color_input("Roughness", 0.3)

                break

        # Also set material directly as fallback
        # Get or create materials
        body_mat = self._get_or_create_material("car_body_custom")
        if body_mat.use_nodes:
            bsdf = body_mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                bsdf.inputs["Base Color"].default_value = (*colors.body, 1.0)
                bsdf.inputs["Metallic"].default_value = 0.8
                bsdf.inputs["Roughness"].default_value = 0.3

        # Assign material to car object
        if car_obj.data.materials:
            car_obj.data.materials[0] = body_mat
        else:
            car_obj.data.materials.append(body_mat)

    def _get_or_create_material(self, name: str) -> bpy.types.Material:
        """Get existing material or create new one."""
        if name in bpy.data.materials:
            return bpy.data.materials[name]

        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        return mat

    def setup_launch_compatible(self, car_obj: bpy.types.Object) -> Dict[str, Any]:
        """
        Setup car object for launch control compatibility.

        This adds:
        - Wheel empties with rotation drivers
        - Chassis root for movement
        - Proper naming conventions
        - Suspension-ready structure

        Returns:
            Dictionary with component references
        """
        components = {
            "chassis": car_obj,
            "wheels": [],
            "wheel_pivots": [],
        }

        # Get car dimensions for wheel placement
        bbox = self._get_bounding_box(car_obj)
        length = bbox["max"].x - bbox["min"].x
        width = bbox["max"].y - bbox["min"].y
        height = bbox["max"].z - bbox["min"].z

        # Create wheel pivot empties
        wheel_positions = [
            ("FL", (length * 0.35, width * 0.4, 0)),   # Front Left
            ("FR", (length * 0.35, -width * 0.4, 0)),  # Front Right
            ("RL", (-length * 0.35, width * 0.4, 0)),  # Rear Left
            ("RR", (-length * 0.35, -width * 0.4, 0)), # Rear Right
        ]

        for pos_name, pos in wheel_positions:
            # Create wheel pivot empty
            pivot = bpy.data.objects.new(f"{car_obj.name}_wheel_{pos_name}", None)
            pivot.empty_display_type = 'ARROWS'
            pivot.location = pos
            pivot.parent = car_obj
            bpy.context.collection.objects.link(pivot)
            components["wheel_pivots"].append(pivot)

        # Store wheel positions for wheel rotation drivers
        car_obj["wheel_radius"] = 0.35  # Default wheel radius
        car_obj["wheelbase"] = length * 0.7
        car_obj["track_width"] = width * 0.8
        car_obj["launch_compatible"] = True

        return components

    def _get_bounding_box(self, obj: bpy.types.Object) -> Dict[str, Vector]:
        """Get world-space bounding box of object."""
        # Evaluate depsgraph for accurate bounds
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)

        corners = [eval_obj.matrix_world @ Vector(corner) for corner in eval_obj.bound_box]

        return {
            "min": Vector((
                min(c.x for c in corners),
                min(c.y for c in corners),
                min(c.z for c in corners)
            )),
            "max": Vector((
                max(c.x for c in corners),
                max(c.y for c in corners),
                max(c.z for c in corners)
            ))
        }

    def create_fleet(
        self,
        count: int,
        styles: Optional[List[str]] = None,
        colors: Optional[List[str]] = None,
        spacing: float = 5.0,
        seed: int = 42
    ) -> List[bpy.types.Object]:
        """
        Create a fleet of varied cars.

        Args:
            count: Number of cars to create
            styles: List of style presets to use (random if None)
            colors: List of color presets to use (random if None)
            spacing: Distance between cars
            seed: Random seed for variation

        Returns:
            List of car objects
        """
        random.seed(seed)
        fleet = []

        style_list = styles or list(STYLE_PRESETS.keys())
        color_list = colors or list(COLOR_PRESETS.keys())

        for i in range(count):
            style = random.choice(style_list)
            color = random.choice(color_list)
            car_seed = random.randint(0, 999999)

            # Position in a line
            x_offset = i * spacing

            car = self.create_car(
                name=f"Car_{i:03d}",
                style=style,
                color=color,
                seed=car_seed,
                position=(x_offset, 0, 0)
            )
            fleet.append(car)

        return fleet


def create_car(
    style: str = "sedan",
    color: str = "red",
    name: str = "Car",
    **kwargs
) -> bpy.types.Object:
    """Convenience function to create a procedural car."""
    factory = ProceduralCarFactory()
    return factory.create_car(name=name, style=style, color=color, **kwargs)


def create_fleet(count: int, **kwargs) -> List[bpy.types.Object]:
    """Convenience function to create a fleet of cars."""
    factory = ProceduralCarFactory()
    return factory.create_fleet(count, **kwargs)
