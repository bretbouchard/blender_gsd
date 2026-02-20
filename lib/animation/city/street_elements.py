"""
Street Elements - Lights, Signs, Banners, and Street Furniture

Creates procedural street elements for city scenes.

Usage:
    from lib.animation.city.street_elements import (
        StreetLightSystem, create_street_lights,
        SignGenerator, create_signs,
        BannerSystem
    )

    # Create street lights along a road
    lights = create_street_lights(
        road_curve=main_road,
        spacing=25.0,
        style="modern",
        side="both"
    )

    # Create traffic signs
    signs = create_signs(
        positions=[(0, 0), (100, 0), (200, 0)],
        types=["stop", "speed_limit", "turn_restriction"]
    )
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING
from pathlib import Path
import math
import random

# Guarded bpy import
try:
    import bpy
    from mathutils import Vector, Matrix
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    Vector = None
    Matrix = None
    BLENDER_AVAILABLE = False


@dataclass
class StreetLightConfig:
    """Configuration for a street light."""
    pole_height: float = 8.0
    pole_diameter: float = 0.25
    arm_length: float = 2.0
    fixture_size: float = 0.6
    light_power: float = 1000.0  # Watts
    light_color: Tuple[float, float, float] = (1.0, 0.95, 0.85)  # Warm white
    style: str = "modern"  # modern, traditional, ornate, highway


@dataclass
class SignConfig:
    """Configuration for a traffic sign."""
    sign_type: str
    width: float = 0.6
    height: float = 0.6
    pole_height: float = 2.5
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    text: str = ""
    reflective: bool = True


# Street element presets
STREET_ELEMENT_PRESETS = {
    "street_light_modern": StreetLightConfig(
        pole_height=10.0,
        style="modern",
        light_power=1500.0,
    ),
    "street_light_traditional": StreetLightConfig(
        pole_height=7.0,
        arm_length=1.5,
        style="traditional",
        light_power=800.0,
    ),
    "street_light_highway": StreetLightConfig(
        pole_height=15.0,
        arm_length=4.0,
        fixture_size=1.0,
        style="highway",
        light_power=2000.0,
    ),
    "stop_sign": SignConfig(
        sign_type="stop",
        color=(0.8, 0.0, 0.0),
        text="STOP",
    ),
    "speed_limit": SignConfig(
        sign_type="regulatory",
        color=(1.0, 1.0, 1.0),
        text="35",
    ),
    "street_name": SignConfig(
        sign_type="street_name",
        width=1.2,
        height=0.3,
        color=(0.1, 0.3, 0.1),
    ),
}


class StreetLightSystem:
    """
    Procedural street light generator.

    Creates street lights along roads with proper spacing
    and lighting setup.
    """

    def __init__(self, config: Optional[StreetLightConfig] = None):
        self.config = config or StreetLightConfig()

    def create_light(
        self,
        position: Tuple[float, float, float],
        rotation: float = 0.0,
        name: str = "StreetLight"
    ) -> Optional[Any]:
        """Create a single street light."""
        if not BLENDER_AVAILABLE:
            return None

        # Create collection for light assembly
        light_collection = bpy.data.collections.new(name)
        bpy.context.collection.children.link(light_collection)

        # Create pole
        bpy.ops.mesh.primitive_cylinder_add(
            radius=self.config.pole_diameter / 2,
            depth=self.config.pole_height,
            location=(position[0], position[1], position[2] + self.config.pole_height / 2)
        )
        pole = bpy.context.active_object
        pole.name = f"{name}_Pole"
        light_collection.objects.link(pole)
        bpy.context.collection.objects.unlink(pole)

        # Create arm
        arm_end_x = position[0] + self.config.arm_length * math.cos(rotation)
        arm_end_y = position[1] + self.config.arm_length * math.sin(rotation)

        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.05,
            depth=self.config.arm_length,
            location=(
                position[0] + self.config.arm_length / 2 * math.cos(rotation),
                position[1] + self.config.arm_length / 2 * math.sin(rotation),
                position[2] + self.config.pole_height
            ),
            rotation=(0, math.radians(90), rotation)
        )
        arm = bpy.context.active_object
        arm.name = f"{name}_Arm"
        light_collection.objects.link(arm)
        bpy.context.collection.objects.unlink(arm)

        # Create fixture
        bpy.ops.mesh.primitive_cube_add(
            size=self.config.fixture_size,
            location=(
                arm_end_x,
                arm_end_y,
                position[2] + self.config.pole_height - self.config.fixture_size / 2
            )
        )
        fixture = bpy.context.active_object
        fixture.name = f"{name}_Fixture"
        fixture.scale = (1, 1, 0.3)
        light_collection.objects.link(fixture)
        bpy.context.collection.objects.unlink(fixture)

        # Create point light
        light_data = bpy.data.lights.new(f"{name}_Light", type='POINT')
        light_data.energy = self.config.light_power
        light_data.color = self.config.light_color
        light_data.shadow_soft_size = 0.5

        light_obj = bpy.data.objects.new(f"{name}_Lamp", light_data)
        light_obj.location = (
            arm_end_x,
            arm_end_y,
            position[2] + self.config.pole_height - self.config.fixture_size
        )
        light_collection.objects.link(light_obj)

        # Apply materials
        self._apply_materials(pole, fixture)

        return light_collection

    def _apply_materials(self, pole: Any, fixture: Any) -> None:
        """Apply materials to street light components."""
        if not BLENDER_AVAILABLE:
            return

        # Pole material (dark gray)
        pole_mat = bpy.data.materials.new("StreetLight_Pole")
        pole_mat.use_nodes = True
        bsdf = pole_mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.2, 0.2, 0.2, 1.0)
            bsdf.inputs["Metallic"].default_value = 0.8

        if pole.data.materials:
            pole.data.materials[0] = pole_mat
        else:
            pole.data.materials.append(pole_mat)

        # Fixture material (light gray)
        fixture_mat = bpy.data.materials.new("StreetLight_Fixture")
        fixture_mat.use_nodes = True
        bsdf = fixture_mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.7, 0.7, 0.7, 1.0)

        if fixture.data.materials:
            fixture.data.materials[0] = fixture_mat
        else:
            fixture.data.materials.append(fixture_mat)


class SignGenerator:
    """Procedural traffic sign generator."""

    SIGN_SHAPES = {
        "stop": "octagon",
        "yield": "triangle_down",
        "speed_limit": "circle",
        "regulatory": "circle",
        "warning": "diamond",
        "guide": "rectangle",
        "street_name": "rectangle",
        "turn_restriction": "circle",
    }

    def create_sign(
        self,
        position: Tuple[float, float, float],
        config: SignConfig,
        name: str = "Sign"
    ) -> Optional[Any]:
        """Create a traffic sign."""
        if not BLENDER_AVAILABLE:
            return None

        # Create pole
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.05,
            depth=config.pole_height,
            location=(position[0], position[1], position[2] + config.pole_height / 2)
        )
        pole = bpy.context.active_object
        pole.name = f"{name}_Pole"

        # Create sign face based on shape
        shape = self.SIGN_SHAPES.get(config.sign_type, "rectangle")

        if shape == "octagon":
            bpy.ops.mesh.primitive_circle_add(
                vertices=8,
                radius=config.width / 2,
                fill_type='NGON',
                location=(position[0], position[1], position[2] + config.pole_height + config.height / 2)
            )
        elif shape == "circle":
            bpy.ops.mesh.primitive_circle_add(
                vertices=32,
                radius=config.width / 2,
                fill_type='NGON',
                location=(position[0], position[1], position[2] + config.pole_height + config.height / 2)
            )
        elif shape == "diamond":
            bpy.ops.mesh.primitive_cube_add(
                size=config.width,
                location=(position[0], position[1], position[2] + config.pole_height + config.height / 2)
            )
            sign = bpy.context.active_object
            sign.rotation_euler[2] = math.pi / 4
        else:  # rectangle
            bpy.ops.mesh.primitive_plane_add(
                size=1,
                location=(position[0], position[1], position[2] + config.pole_height + config.height / 2)
            )
            sign = bpy.context.active_object
            sign.scale = (config.width, config.height, 1)

        sign = bpy.context.active_object
        sign.name = f"{name}_Face"

        # Apply sign material
        self._apply_sign_material(sign, config)

        # Parent sign to pole
        sign.parent = pole

        return pole

    def _apply_sign_material(self, sign: Any, config: SignConfig) -> None:
        """Apply sign face material."""
        if not BLENDER_AVAILABLE:
            return

        mat = bpy.data.materials.new(f"Sign_{config.sign_type}")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*config.color, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.3 if config.reflective else 0.7

        if sign.data.materials:
            sign.data.materials[0] = mat
        else:
            sign.data.materials.append(mat)


class BannerSystem:
    """Street banner and decoration system."""

    def create_banner(
        self,
        position: Tuple[float, float, float],
        width: float = 1.0,
        height: float = 3.0,
        text: str = "",
        color: Tuple[float, float, float] = (0.8, 0.2, 0.2)
    ) -> Optional[Any]:
        """Create a street banner."""
        if not BLENDER_AVAILABLE:
            return None

        # Create banner mesh
        bpy.ops.mesh.primitive_plane_add(
            size=1,
            location=position
        )
        banner = bpy.context.active_object
        banner.scale = (width / 10, 0.02, height / 10)
        banner.rotation_euler = (math.pi / 2, 0, 0)
        banner.name = "Street_Banner"

        # Apply material
        mat = bpy.data.materials.new("Banner_Material")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*color, 1.0)

        if banner.data.materials:
            banner.data.materials[0] = mat
        else:
            banner.data.materials.append(mat)

        return banner


class UtilitySystem:
    """Utility poles, power lines, street furniture."""

    def create_utility_pole(
        self,
        position: Tuple[float, float, float],
        height: float = 12.0,
        arms: int = 2
    ) -> Optional[Any]:
        """Create a utility pole with cross arms."""
        if not BLENDER_AVAILABLE:
            return None

        # Main pole
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.15,
            depth=height,
            location=(position[0], position[1], position[2] + height / 2)
        )
        pole = bpy.context.active_object
        pole.name = "Utility_Pole"

        # Cross arms
        for i in range(arms):
            arm_height = height * (0.6 + i * 0.15)
            arm_length = 2.0

            bpy.ops.mesh.primitive_cube_add(
                size=1,
                location=(position[0], position[1], position[2] + arm_height)
            )
            arm = bpy.context.active_object
            arm.scale = (arm_length, 0.1, 0.1)
            arm.name = f"CrossArm_{i}"
            arm.parent = pole

        return pole


def create_street_lights(
    road_curve: Any,
    spacing: float = 25.0,
    style: str = "modern",
    side: str = "both",
    offset: float = 3.0
) -> List[Any]:
    """
    Create street lights along a road curve.

    Args:
        road_curve: Blender curve object representing the road
        spacing: Distance between lights in meters
        style: Light style preset
        side: "left", "right", or "both"
        offset: Distance from road edge

    Returns:
        List of created light objects
    """
    if not BLENDER_AVAILABLE:
        return []

    config = STREET_ELEMENT_PRESETS.get(
        f"street_light_{style}",
        StreetLightConfig()
    )
    system = StreetLightSystem(config)

    lights = []

    # Get curve length and sample points
    # For now, create lights at regular intervals
    curve_length = 500.0  # Would calculate from curve
    num_lights = int(curve_length / spacing)

    for i in range(num_lights):
        t = i / num_lights
        # Would interpolate position along curve
        x = t * curve_length
        y = offset if side in ["right", "both"] else -offset

        light = system.create_light(
            position=(x, y, 0),
            rotation=0 if side == "right" else math.pi,
            name=f"StreetLight_{i:03d}"
        )

        if light:
            lights.append(light)

        if side == "both":
            light = system.create_light(
                position=(x, -y, 0),
                rotation=math.pi,
                name=f"StreetLight_{i:03d}_L"
            )
            if light:
                lights.append(light)

    return lights


def create_signs(
    positions: List[Tuple[float, float]],
    types: List[str],
    **kwargs
) -> List[Any]:
    """
    Create traffic signs at specified positions.

    Args:
        positions: List of (x, y) positions
        types: List of sign types

    Returns:
        List of created sign objects
    """
    if not BLENDER_AVAILABLE:
        return []

    gen = SignGenerator()
    signs = []

    for i, (pos, sign_type) in enumerate(zip(positions, types)):
        config = SignConfig(
            sign_type=sign_type,
            text=kwargs.get("text", "")
        )

        sign = gen.create_sign(
            position=(pos[0], pos[1], 0),
            config=config,
            name=f"Sign_{i:03d}"
        )

        if sign:
            signs.append(sign)

    return signs
