"""
Highway Light Pole Generator

Generates street lighting infrastructure:
- Highway cobra head lights
- Ramp/exit lighting
- Overhead gantry lights
- Decorative urban lights

Includes automatic placement along road networks.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
import math
import random

try:
    import bpy
    import bmesh
    from bpy.types import Object, Collection, Light
    from mathutils import Vector
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Object = Any
    Collection = Any
    Light = Any


class PoleType(Enum):
    """Types of light poles."""
    HIGHWAY_COBRA = "cobra"           # Standard highway cobra head
    HIGHWAY_DOUBLE = "double_cobra"   # Double arm for wide roads
    RAMP_LIGHT = "ramp"               # Smaller ramp/exit lights
    GANTRY_LIGHT = "gantry"           # Overhead sign lights
    URBAN_DECORATIVE = "urban"        # Decorative city lights
    PARKING_LOT = "parking"           # Shoebox parking lot lights


@dataclass
class LightPoleConfig:
    """Configuration for light pole generation."""
    # Pole dimensions (meters)
    pole_height: float = 10.0
    pole_diameter_base: float = 0.35
    pole_diameter_top: float = 0.15
    pole_taper: float = 0.5  # Taper ratio

    # Arm dimensions
    arm_length: float = 2.0
    arm_diameter: float = 0.08
    arm_angle: float = 15.0  # Degrees below horizontal

    # Luminaire (light fixture)
    luminaire_length: float = 0.8
    luminaire_width: float = 0.3
    luminaire_height: float = 0.25

    # Light settings
    light_power: float = 1000.0  # Watts
    light_color: Tuple[float, float, float] = (1.0, 0.95, 0.85)  # Warm white
    light_temperature: int = 3000  # Kelvin (for reference)

    # Spacing
    spacing: float = 50.0  # Meters between poles

    # Materials
    pole_color: Tuple[float, float, float] = (0.3, 0.3, 0.3)  # Dark gray
    luminaire_color: Tuple[float, float, float] = (0.7, 0.7, 0.7)  # Light gray


# Standard configurations for different pole types
POLE_CONFIGS = {
    PoleType.HIGHWAY_COBRA: LightPoleConfig(
        pole_height=12.0,
        pole_diameter_base=0.40,
        pole_diameter_top=0.18,
        arm_length=2.5,
        light_power=1500.0,
        spacing=60.0,
    ),
    PoleType.HIGHWAY_DOUBLE: LightPoleConfig(
        pole_height=14.0,
        pole_diameter_base=0.45,
        arm_length=3.0,
        light_power=2000.0,
        spacing=70.0,
    ),
    PoleType.RAMP_LIGHT: LightPoleConfig(
        pole_height=8.0,
        pole_diameter_base=0.25,
        arm_length=1.5,
        light_power=400.0,
        spacing=30.0,
    ),
    PoleType.GANTRY_LIGHT: LightPoleConfig(
        pole_height=0.5,  # Mounted on gantry
        arm_length=0.0,   # Direct mount
        luminaire_length=0.6,
        light_power=600.0,
    ),
    PoleType.URBAN_DECORATIVE: LightPoleConfig(
        pole_height=6.0,
        pole_diameter_base=0.20,
        pole_diameter_top=0.12,
        arm_length=0.8,
        light_power=250.0,
        spacing=20.0,
        pole_color=(0.15, 0.15, 0.15),  # Black
    ),
    PoleType.PARKING_LOT: LightPoleConfig(
        pole_height=9.0,
        arm_length=0.0,  # Shoebox style
        luminaire_length=1.2,
        luminaire_width=0.4,
        light_power=750.0,
        spacing=40.0,
    ),
}


class LightPoleGenerator:
    """
    Generates highway light pole geometry with functional lights.

    Creates realistic light poles with proper dimensions and materials.
    """

    def __init__(self):
        """Initialize the light pole generator."""
        self._material_cache: Dict[str, Any] = {}
        self._light_count = 0

    def create_pole(
        self,
        pole_type: PoleType = PoleType.HIGHWAY_COBRA,
        config: Optional[LightPoleConfig] = None,
        name: str = "Highway_Light",
    ) -> Optional[Object]:
        """
        Create a single light pole.

        Args:
            pole_type: Type of light pole
            config: Custom configuration (overrides preset)
            name: Object name

        Returns:
            Blender object (parent empty with children)
        """
        if not BLENDER_AVAILABLE:
            return None

        config = config or POLE_CONFIGS.get(pole_type, LightPoleConfig())

        # Create parent empty
        pole_obj = bpy.data.objects.new(name, None)
        pole_obj.empty_display_type = "PLAIN_AXES"

        # Create pole shaft
        shaft = self._create_pole_shaft(config, f"{name}_Shaft")
        if shaft:
            shaft.parent = pole_obj

        # Create arm (if applicable)
        if config.arm_length > 0:
            arm = self._create_arm(config, f"{name}_Arm")
            if arm:
                arm.location = (0, 0, config.pole_height)
                arm.parent = pole_obj

        # Create luminaire and light
        luminaire = self._create_luminaire(config, f"{name}_Luminaire")
        if luminaire:
            if pole_type == PoleType.PARKING_LOT:
                # Shoebox style - mounted directly on pole
                luminaire.location = (0, config.luminaire_length/2, config.pole_height)
            else:
                # Cobra head style - at end of arm
                luminaire.location = (config.arm_length, 0, config.pole_height)
            luminaire.rotation_euler = (math.radians(-config.arm_angle), 0, 0)
            luminaire.parent = pole_obj

        # Create actual light
        light = self._create_light(config, f"{name}_Point")
        if light:
            light.location = (config.arm_length if config.arm_length > 0 else 0, 0, config.pole_height - 0.1)
            light.parent = pole_obj

        return pole_obj

    def create_double_pole(
        self,
        config: Optional[LightPoleConfig] = None,
        name: str = "Double_Light",
    ) -> Optional[Object]:
        """
        Create a double-arm light pole (both sides).

        Args:
            config: Pole configuration
            name: Object name

        Returns:
            Blender object
        """
        if not BLENDER_AVAILABLE:
            return None

        config = config or POLE_CONFIGS[PoleType.HIGHWAY_DOUBLE]

        # Create parent
        pole_obj = bpy.data.objects.new(name, None)
        pole_obj.empty_display_type = "PLAIN_AXES"

        # Create pole shaft
        shaft = self._create_pole_shaft(config, f"{name}_Shaft")
        if shaft:
            shaft.parent = pole_obj

        # Create two arms (opposite sides)
        for side, sign in [("L", 1), ("R", -1)]:
            arm = self._create_arm(config, f"{name}_Arm_{side}")
            if arm:
                arm.location = (0, 0, config.pole_height)
                arm.rotation_euler = (0, 0, math.radians(sign * 90))
                arm.parent = pole_obj

            luminaire = self._create_luminaire(config, f"{name}_Luminaire_{side}")
            if luminaire:
                luminaire.location = (0, sign * config.arm_length, config.pole_height)
                luminaire.rotation_euler = (math.radians(-config.arm_angle), 0, math.radians(sign * 90))
                luminaire.parent = pole_obj

            light = self._create_light(config, f"{name}_Light_{side}")
            if light:
                light.location = (0, sign * config.arm_length, config.pole_height - 0.1)
                light.parent = pole_obj

        return pole_obj

    def _create_pole_shaft(
        self,
        config: LightPoleConfig,
        name: str,
    ) -> Optional[Object]:
        """Create tapered pole shaft."""
        if not BLENDER_AVAILABLE:
            return None

        # Use cone primitive for tapered pole
        bpy.ops.mesh.primitive_cone_add(
            radius1=config.pole_diameter_base / 2,
            radius2=config.pole_diameter_top / 2,
            depth=config.pole_height,
            location=(0, 0, config.pole_height / 2),
        )
        shaft = bpy.context.active_object
        shaft.name = name

        # Apply metal material
        mat = self._get_pole_material(config)
        if mat:
            shaft.data.materials.append(mat)

        return shaft

    def _create_arm(
        self,
        config: LightPoleConfig,
        name: str,
    ) -> Optional[Object]:
        """Create light arm."""
        if not BLENDER_AVAILABLE:
            return None

        # Create arm as curved section
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        bm = bmesh.new()

        # Simple curved arm
        segments = 8
        curve_height = 0.3  # Arm curves down slightly

        for i in range(segments + 1):
            t = i / segments
            x = t * config.arm_length
            z = -curve_height * t * t  # Parabolic curve

            # Create circle of vertices at this position
            angle_offset = t * 0.1  # Slight twist
            for j in range(8):
                angle = (j / 8) * 2 * math.pi + angle_offset
                r = config.arm_diameter / 2 * (1 - t * 0.2)  # Taper
                y = r * math.cos(angle)
                z_offset = r * math.sin(angle)

                bm.verts.new((x, y, z + z_offset))

        bm.verts.ensure_lookup_table()

        # Create faces connecting rings
        for i in range(segments):
            for j in range(8):
                v1 = bm.verts[i * 8 + j]
                v2 = bm.verts[i * 8 + (j + 1) % 8]
                v3 = bm.verts[(i + 1) * 8 + (j + 1) % 8]
                v4 = bm.verts[(i + 1) * 8 + j]
                bm.faces.new([v1, v2, v3, v4])

        # Cap ends
        bm.faces.new([bm.verts[j] for j in range(8)])  # Base cap
        last_start = segments * 8
        bm.faces.new([bm.verts[last_start + j] for j in range(7, -1, -1)])  # End cap

        bm.to_mesh(mesh)
        bm.free()

        mat = self._get_pole_material(config)
        if mat:
            obj.data.materials.append(mat)

        return obj

    def _create_luminaire(
        self,
        config: LightPoleConfig,
        name: str,
    ) -> Optional[Object]:
        """Create the light fixture (cobra head or shoebox)."""
        if not BLENDER_AVAILABLE:
            return None

        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        bm = bmesh.new()

        # Cobra head shape
        hl = config.luminaire_length / 2
        hw = config.luminaire_width / 2
        hh = config.luminaire_height / 2

        # Main body vertices
        verts = [
            (-hl, -hw, 0),          # 0: back-bottom-left
            (hl, -hw, 0),           # 1: front-bottom-left
            (hl, hw, 0),            # 2: front-bottom-right
            (-hl, hw, 0),           # 3: back-bottom-right
            (-hl * 0.8, -hw * 0.8, hh),    # 4: back-top-left
            (hl * 0.6, -hw * 0.8, hh),     # 5: front-top-left
            (hl * 0.6, hw * 0.8, hh),      # 6: front-top-right
            (-hl * 0.8, hw * 0.8, hh),     # 7: back-top-right
            (-hl * 0.3, -hw * 0.3, hh * 1.3),  # 8: very top for curve
            (hl * 0.2, -hw * 0.3, hh * 1.2),
            (hl * 0.2, hw * 0.3, hh * 1.2),
            (-hl * 0.3, hw * 0.3, hh * 1.3),
        ]

        for v in verts:
            bm.verts.new(v)

        bm.verts.ensure_lookup_table()

        # Bottom face (glass lens)
        bm.faces.new([bm.verts[0], bm.verts[3], bm.verts[2], bm.verts[1]])

        # Side faces
        bm.faces.new([bm.verts[0], bm.verts[1], bm.verts[5], bm.verts[4]])  # Left
        bm.faces.new([bm.verts[1], bm.verts[2], bm.verts[6], bm.verts[5]])  # Front
        bm.faces.new([bm.verts[2], bm.verts[3], bm.verts[7], bm.verts[6]])  # Right
        bm.faces.new([bm.verts[3], bm.verts[0], bm.verts[4], bm.verts[7]])  # Back

        # Top faces
        bm.faces.new([bm.verts[4], bm.verts[5], bm.verts[9], bm.verts[8]])
        bm.faces.new([bm.verts[5], bm.verts[6], bm.verts[10], bm.verts[9]])
        bm.faces.new([bm.verts[6], bm.verts[7], bm.verts[11], bm.verts[10]])
        bm.faces.new([bm.verts[7], bm.verts[4], bm.verts[8], bm.verts[11]])
        bm.faces.new([bm.verts[8], bm.verts[9], bm.verts[10], bm.verts[11]])

        bm.to_mesh(mesh)
        bm.free()

        # Apply material
        mat = self._get_luminaire_material(config)
        if mat:
            obj.data.materials.append(mat)

        return obj

    def _create_light(
        self,
        config: LightPoleConfig,
        name: str,
    ) -> Optional[Object]:
        """Create the actual point light."""
        if not BLENDER_AVAILABLE:
            return None

        self._light_count += 1

        # Create light data
        light_data = bpy.data.lights.new(name=name, type='POINT')
        light_data.energy = config.light_power
        light_data.color = config.light_color
        light_data.shadow_soft_size = 0.5

        # Create light object
        light_obj = bpy.data.objects.new(name, light_data)

        return light_obj

    def _get_pole_material(self, config: LightPoleConfig) -> Optional[Any]:
        """Get or create pole material."""
        if not BLENDER_AVAILABLE:
            return None

        cache_key = f"pole_{config.pole_color}"
        if cache_key in self._material_cache:
            return self._material_cache[cache_key]

        mat = bpy.data.materials.new("Light_Pole_Metal")
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*config.pole_color, 1.0)
            bsdf.inputs["Metallic"].default_value = 0.8
            bsdf.inputs["Roughness"].default_value = 0.4

        self._material_cache[cache_key] = mat
        return mat

    def _get_luminaire_material(self, config: LightPoleConfig) -> Optional[Any]:
        """Get or create luminaire material."""
        if not BLENDER_AVAILABLE:
            return None

        if "luminaire" in self._material_cache:
            return self._material_cache["luminaire"]

        mat = bpy.data.materials.new("Luminaire_Housing")
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*config.luminaire_color, 1.0)
            bsdf.inputs["Metallic"].default_value = 0.3
            bsdf.inputs["Roughness"].default_value = 0.5

        self._material_cache["luminaire"] = mat
        return mat


def create_highway_light(
    height: float = 12.0,
    name: str = "Highway_Light",
) -> Optional[Object]:
    """
    Create a standard highway cobra head light.

    Args:
        height: Pole height in meters
        name: Object name

    Returns:
        Blender object
    """
    config = LightPoleConfig(pole_height=height)
    generator = LightPoleGenerator()
    return generator.create_pole(PoleType.HIGHWAY_COBRA, config, name)


def place_lights_along_road(
    road_points: List[Tuple[float, float, float]],
    offset: float = 5.0,
    side: str = "right",
    pole_type: PoleType = PoleType.HIGHWAY_COBRA,
    config: Optional[LightPoleConfig] = None,
    collection: Optional[Collection] = None,
) -> List[Object]:
    """
    Place light poles along a road path.

    Args:
        road_points: Center line points of the road
        offset: Distance from road center
        side: "left" or "right" side of road
        pole_type: Type of light pole
        config: Pole configuration
        collection: Collection to add objects to

    Returns:
        List of created light pole objects
    """
    if not BLENDER_AVAILABLE or len(road_points) < 2:
        return []

    config = config or POLE_CONFIGS.get(pole_type, LightPoleConfig())
    generator = LightPoleGenerator()
    objects = []

    offset_sign = 1 if side == "right" else -1

    # Calculate total path length and place poles
    total_length = 0.0
    segment_lengths = []

    for i in range(len(road_points) - 1):
        p1 = Vector(road_points[i])
        p2 = Vector(road_points[i + 1])
        length = (p2 - p1).length
        segment_lengths.append(length)
        total_length += length

    # Place poles at regular intervals
    current_distance = 0.0
    next_pole_distance = config.spacing / 2  # Start half-spacing from beginning

    for i, (p1, p2) in enumerate(zip(road_points[:-1], road_points[1:])):
        p1_v = Vector(p1)
        p2_v = Vector(p2)
        direction = (p2_v - p1_v).normalized()
        segment_length = segment_lengths[i]

        perpendicular = Vector((-direction.y, direction.x, 0))

        while next_pole_distance <= current_distance + segment_length:
            # Calculate position along this segment
            t = (next_pole_distance - current_distance) / segment_length
            position = p1_v + direction * (segment_length * t)

            # Offset to side of road
            pole_pos = position + perpendicular * offset * offset_sign

            # Create pole
            pole = generator.create_pole(pole_type, config, f"RoadLight_{len(objects)}")
            if pole:
                pole.location = pole_pos

                # Rotate to face road
                angle = math.atan2(direction.y, direction.x)
                pole.rotation_euler = (0, 0, angle - math.pi/2)

                if collection:
                    collection.objects.link(pole)

                objects.append(pole)

            next_pole_distance += config.spacing

        current_distance += segment_length

    return objects


def create_lighted_intersection(
    center: Tuple[float, float, float] = (0, 0, 0),
    radius: float = 20.0,
    collection: Optional[Collection] = None,
) -> List[Object]:
    """
    Create light poles for a highway intersection.

    Places 4 poles at corners of intersection.

    Args:
        center: Center of intersection
        radius: Distance from center to poles
        collection: Collection to add to

    Returns:
        List of created objects
    """
    if not BLENDER_AVAILABLE:
        return []

    generator = LightPoleGenerator()
    objects = []

    positions = [
        (radius, radius),
        (-radius, radius),
        (-radius, -radius),
        (radius, -radius),
    ]

    for i, (x, y) in enumerate(positions):
        pole = generator.create_pole(
            PoleType.HIGHWAY_COBRA,
            name=f"IntersectionLight_{i}"
        )
        if pole:
            pole.location = (center[0] + x, center[1] + y, center[2])

            if collection:
                collection.objects.link(pole)

            objects.append(pole)

    return objects


__all__ = [
    "PoleType",
    "LightPoleConfig",
    "POLE_CONFIGS",
    "LightPoleGenerator",
    "create_highway_light",
    "place_lights_along_road",
    "create_lighted_intersection",
]
