"""
Hero Car Model Generator

Creates the main chase vehicle:
- Procedural car body mesh
- Wheel assemblies
- Detail components (mirrors, lights, grill)
- Car paint materials

Designed for cinematic car chase sequences.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
import math

try:
    import bpy
    import bmesh
    from bpy.types import Object, Collection
    from mathutils import Vector, Matrix
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Object = Any
    Collection = Any


class CarType(Enum):
    """Types of vehicles."""
    SEDAN = "sedan"           # Standard 4-door sedan
    SPORTS = "sports"         # Sports car
    SUV = "suv"               # SUV/Crossover
    MUSCLE = "muscle"         # Muscle car
    TRUCK = "truck"           # Pickup truck
    POLICE = "police"         # Police cruiser


@dataclass
class CarDimensions:
    """Physical dimensions for car model."""
    # Overall
    length: float = 4.8       # Meters
    width: float = 1.9
    height: float = 1.4
    wheelbase: float = 2.8
    ground_clearance: float = 0.15

    # Body proportions
    hood_length: float = 1.2
    cabin_length: float = 2.0
    trunk_length: float = 1.0
    roof_height: float = 0.6

    # Wheels
    wheel_radius: float = 0.35
    wheel_width: float = 0.25
    front_track: float = 1.6
    rear_track: float = 1.6


@dataclass
class CarPaintConfig:
    """Configuration for car paint material."""
    base_color: Tuple[float, float, float] = (0.1, 0.1, 0.15)  # Dark blue
    metallic: float = 0.8
    roughness: float = 0.2
    clearcoat: float = 1.0
    clearcoat_roughness: float = 0.03

    # Special effects
    flip_flop: bool = False    # Color-shifting paint
    flip_color: Tuple[float, float, float] = (0.3, 0.2, 0.4)


# Car type presets
CAR_DIMENSIONS = {
    CarType.SEDAN: CarDimensions(
        length=4.8, width=1.85, height=1.45,
        wheelbase=2.8, wheel_radius=0.32,
    ),
    CarType.SPORTS: CarDimensions(
        length=4.5, width=1.95, height=1.25,
        wheelbase=2.6, wheel_radius=0.35,
        ground_clearance=0.12,
    ),
    CarType.SUV: CarDimensions(
        length=5.0, width=2.0, height=1.8,
        wheelbase=3.0, wheel_radius=0.4,
        ground_clearance=0.22,
    ),
    CarType.MUSCLE: CarDimensions(
        length=5.0, width=1.95, height=1.35,
        wheelbase=2.85, wheel_radius=0.36,
        hood_length=1.5,
    ),
    CarType.TRUCK: CarDimensions(
        length=5.5, width=2.0, height=1.9,
        wheelbase=3.4, wheel_radius=0.42,
        ground_clearance=0.25,
    ),
    CarType.POLICE: CarDimensions(
        length=5.1, width=1.95, height=1.5,
        wheelbase=2.95, wheel_radius=0.36,
    ),
}

# Paint color presets
PAINT_PRESETS = {
    "midnight_blue": CarPaintConfig(
        base_color=(0.08, 0.1, 0.2),
        metallic=0.85,
    ),
    "jet_black": CarPaintConfig(
        base_color=(0.02, 0.02, 0.02),
        metallic=0.9,
        roughness=0.15,
    ),
    "cherry_red": CarPaintConfig(
        base_color=(0.6, 0.05, 0.05),
        metallic=0.8,
    ),
    "silver": CarPaintConfig(
        base_color=(0.6, 0.6, 0.62),
        metallic=0.95,
        roughness=0.25,
    ),
    "white": CarPaintConfig(
        base_color=(0.95, 0.95, 0.95),
        metallic=0.1,
        roughness=0.4,
    ),
    "racing_green": CarPaintConfig(
        base_color=(0.05, 0.25, 0.1),
        metallic=0.85,
    ),
}


class HeroCarBuilder:
    """
    Builds procedural hero car models.

    Creates detailed car meshes suitable for cinematic
    close-up shots in chase sequences.
    """

    def __init__(self):
        """Initialize car builder."""
        self._material_cache: Dict[str, Any] = {}

    def create_car(
        self,
        car_type: CarType = CarType.SEDAN,
        dimensions: Optional[CarDimensions] = None,
        paint_config: Optional[CarPaintConfig] = None,
        name: str = "Hero_Car",
    ) -> Optional[Object]:
        """
        Create a hero car model.

        Args:
            car_type: Type of vehicle
            dimensions: Custom dimensions
            paint_config: Paint configuration
            name: Object name

        Returns:
            Blender object (parent with children)
        """
        if not BLENDER_AVAILABLE:
            return None

        dims = dimensions or CAR_DIMENSIONS.get(car_type, CarDimensions())
        paint = paint_config or PAINT_PRESETS["midnight_blue"]

        # Create parent
        car_obj = bpy.data.objects.new(name, None)
        car_obj.empty_display_type = "PLAIN_AXES"

        # Create body
        body = self._create_body(dims, f"{name}_Body")
        if body:
            mat = self._get_car_paint_material(paint)
            if mat:
                body.data.materials.append(mat)
            body.parent = car_obj

        # Create wheels
        for i, (x_offset, name_suffix) in enumerate([
            (dims.wheelbase / 2, "FL"),
            (-dims.wheelbase / 2, "RL"),
            (dims.wheelbase / 2, "FR"),
            (-dims.wheelbase / 2, "RR"),
        ]):
            y_sign = 1 if i < 2 else -1
            wheel = self._create_wheel(dims, f"{name}_Wheel_{name_suffix}")
            if wheel:
                wheel.location = (
                    x_offset,
                    y_sign * dims.front_track / 2,
                    dims.wheel_radius,
                )
                if y_sign < 0:
                    wheel.rotation_euler = (0, 0, math.pi)
                wheel.parent = car_obj

        # Create windows
        windows = self._create_windows(dims, f"{name}_Windows")
        if windows:
            mat = self._get_glass_material()
            if mat:
                windows.data.materials.append(mat)
            windows.parent = car_obj

        # Create headlights
        for side in ["L", "R"]:
            headlight = self._create_headlight(dims, f"{name}_Headlight_{side}")
            if headlight:
                y_offset = dims.width / 2 - 0.15 if side == "L" else -dims.width / 2 + 0.15
                headlight.location = (dims.length / 2 - 0.1, y_offset, dims.height * 0.4)
                if side == "R":
                    headlight.rotation_euler = (0, 0, math.pi)
                headlight.parent = car_obj

        # Create taillights
        for side in ["L", "R"]:
            taillight = self._create_taillight(dims, f"{name}_Taillight_{side}")
            if taillight:
                y_offset = dims.width / 2 - 0.2 if side == "L" else -dims.width / 2 + 0.2
                taillight.location = (-dims.length / 2 + 0.1, y_offset, dims.height * 0.45)
                if side == "R":
                    taillight.rotation_euler = (0, 0, math.pi)
                taillight.parent = car_obj

        return car_obj

    def _create_body(
        self,
        dims: CarDimensions,
        name: str,
    ) -> Optional[Object]:
        """Create car body mesh."""
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        bm = bmesh.new()

        # Body profile points (side view)
        # Key: (x, z) for body outline
        profile = [
            # Front
            (dims.length / 2, dims.ground_clearance),
            (dims.length / 2 - 0.2, dims.height * 0.3),
            (dims.length / 2 - dims.hood_length, dims.height * 0.35),
            # Windshield base
            (dims.length / 2 - dims.hood_length, dims.height * 0.6),
            # Roof
            (dims.length / 2 - dims.hood_length - dims.cabin_length * 0.3, dims.height),
            (dims.length / 2 - dims.hood_length - dims.cabin_length, dims.height),
            # Rear window
            (-dims.length / 2 + dims.trunk_length + 0.3, dims.height * 0.6),
            # Trunk
            (-dims.length / 2 + dims.trunk_length, dims.height * 0.4),
            (-dims.length / 2 + 0.1, dims.height * 0.35),
            (-dims.length / 2, dims.ground_clearance + 0.1),
            # Bottom
            (-dims.length / 2 + 0.3, dims.ground_clearance),
            (dims.length / 2 - 0.3, dims.ground_clearance),
        ]

        # Create body by extruding profile
        half_width = dims.width / 2

        # Create vertices for both sides
        left_verts = []
        right_verts = []

        for x, z in profile:
            # Left side
            v_left = bm.verts.new((x, half_width * 0.95, z))
            left_verts.append(v_left)
            # Right side
            v_right = bm.verts.new((x, -half_width * 0.95, z))
            right_verts.append(v_right)

        bm.verts.ensure_lookup_table()

        # Create faces
        for i in range(len(profile) - 1):
            # Top face (left to right, front to back)
            bm.faces.new([
                left_verts[i],
                left_verts[i + 1],
                right_verts[i + 1],
                right_verts[i],
            ])

        # Front face
        bm.faces.new([left_verts[0], right_verts[0], right_verts[1], left_verts[1]])

        # Rear face
        last = len(profile) - 1
        bm.faces.new([left_verts[last], left_verts[last - 1], right_verts[last - 1], right_verts[last]])

        # Bottom face
        bm.faces.new([
            left_verts[-1], right_verts[-1],
            right_verts[-2], left_verts[-2],
        ])

        bm.to_mesh(mesh)
        bm.free()

        # Smooth shade
        for poly in mesh.polygons:
            poly.use_smooth = True

        return obj

    def _create_wheel(
        self,
        dims: CarDimensions,
        name: str,
    ) -> Optional[Object]:
        """Create wheel mesh."""
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        bm = bmesh.new()

        # Create torus-like wheel
        segments = 24
        radius = dims.wheel_radius
        inner_radius = dims.wheel_radius * 0.6
        width = dims.wheel_width

        # Create outer ring
        for i in range(segments):
            angle = (i / segments) * 2 * math.pi
            next_angle = ((i + 1) / segments) * 2 * math.pi

            # Outer vertices
            v1 = bm.verts.new((
                radius * math.cos(angle),
                -width / 2,
                radius * math.sin(angle),
            ))
            v2 = bm.verts.new((
                radius * math.cos(angle),
                width / 2,
                radius * math.sin(angle),
            ))
            v3 = bm.verts.new((
                radius * math.cos(next_angle),
                width / 2,
                radius * math.sin(next_angle),
            ))
            v4 = bm.verts.new((
                radius * math.cos(next_angle),
                -width / 2,
                radius * math.sin(next_angle),
            ))

        bm.verts.ensure_lookup_table()

        # Create faces for outer ring
        for i in range(segments):
            idx = i * 4
            bm.faces.new([
                bm.verts[idx],
                bm.verts[idx + 1],
                bm.verts[(idx + 5) % (segments * 4)],
                bm.verts[(idx + 4) % (segments * 4)],
            ])

        # Create hub (center disc)
        center_front = bm.verts.new((0, width / 2, 0))
        center_back = bm.verts.new((0, -width / 2, 0))

        for i in range(segments):
            angle = (i / segments) * 2 * math.pi
            next_angle = ((i + 1) / segments) * 2 * math.pi

            # Hub vertices
            hf = bm.verts.new((
                inner_radius * math.cos(angle),
                width / 2,
                inner_radius * math.sin(angle),
            ))
            hb = bm.verts.new((
                inner_radius * math.cos(angle),
                -width / 2,
                inner_radius * math.sin(angle),
            ))

        bm.verts.ensure_lookup_table()

        # Hub faces
        hub_start = segments * 4
        for i in range(segments):
            # Front hub face
            f1 = bm.verts[hub_start + 2 + i * 2]
            f2 = bm.verts[hub_start + 2 + ((i + 1) % segments) * 2]
            bm.faces.new([bm.verts[hub_start], f2, f1])

            # Back hub face
            b1 = bm.verts[hub_start + 1 + i * 2]
            b2 = bm.verts[hub_start + 1 + ((i + 1) % segments) * 2]
            bm.faces.new([bm.verts[hub_start + 1], b1, b2])

        bm.to_mesh(mesh)
        bm.free()

        # Apply wheel material
        mat = self._get_wheel_material()
        if mat:
            obj.data.materials.append(mat)

        return obj

    def _create_windows(
        self,
        dims: CarDimensions,
        name: str,
    ) -> Optional[Object]:
        """Create window glass mesh."""
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        bm = bmesh.new()

        half_width = dims.width / 2 - 0.05

        # Windshield
        ws_front = dims.length / 2 - dims.hood_length
        ws_back = ws_front - dims.cabin_length * 0.3

        # Windshield vertices
        bm.verts.new((ws_front, half_width, dims.height * 0.65))
        bm.verts.new((ws_front, -half_width, dims.height * 0.65))
        bm.verts.new((ws_back, -half_width, dims.height * 0.95))
        bm.verts.new((ws_back, half_width, dims.height * 0.95))

        bm.verts.ensure_lookup_table()
        bm.faces.new([bm.verts[0], bm.verts[1], bm.verts[2], bm.verts[3]])

        # Rear window
        rw_front = -dims.length / 2 + dims.trunk_length + 0.3
        rw_back = -dims.length / 2 + dims.trunk_length

        bm.verts.new((rw_front, half_width, dims.height * 0.95))
        bm.verts.new((rw_front, -half_width, dims.height * 0.95))
        bm.verts.new((rw_back, -half_width, dims.height * 0.65))
        bm.verts.new((rw_back, half_width, dims.height * 0.65))

        bm.verts.ensure_lookup_table()
        bm.faces.new([bm.verts[4], bm.verts[5], bm.verts[6], bm.verts[7]])

        # Side windows (simplified)
        side_ws_x = dims.length / 2 - dims.hood_length - 0.1
        side_rw_x = -dims.length / 2 + dims.trunk_length + 0.4

        # Left side windows
        bm.verts.new((side_ws_x, half_width, dims.height * 0.65))
        bm.verts.new((side_rw_x, half_width, dims.height * 0.65))
        bm.verts.new((side_rw_x, half_width, dims.height * 0.95))
        bm.verts.new((side_ws_x, half_width, dims.height * 0.95))

        bm.verts.ensure_lookup_table()
        bm.faces.new([bm.verts[8], bm.verts[9], bm.verts[10], bm.verts[11]])

        # Right side windows
        bm.verts.new((side_ws_x, -half_width, dims.height * 0.65))
        bm.verts.new((side_rw_x, -half_width, dims.height * 0.65))
        bm.verts.new((side_rw_x, -half_width, dims.height * 0.95))
        bm.verts.new((side_ws_x, -half_width, dims.height * 0.95))

        bm.verts.ensure_lookup_table()
        bm.faces.new([bm.verts[15], bm.verts[14], bm.verts[13], bm.verts[12]])

        bm.to_mesh(mesh)
        bm.free()

        return obj

    def _create_headlight(
        self,
        dims: CarDimensions,
        name: str,
    ) -> Optional[Object]:
        """Create headlight mesh."""
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        bm = bmesh.new()

        # Simple headlight shape
        w, h = 0.15, 0.08

        bm.verts.new((0.05, -w, -h))
        bm.verts.new((0.05, w, -h))
        bm.verts.new((0.05, w, h))
        bm.verts.new((0.05, -w, h))
        bm.verts.new((-0.02, -w * 0.8, -h * 0.8))
        bm.verts.new((-0.02, w * 0.8, -h * 0.8))
        bm.verts.new((-0.02, w * 0.8, h * 0.8))
        bm.verts.new((-0.02, -w * 0.8, h * 0.8))

        bm.verts.ensure_lookup_table()

        # Front face (emissive)
        bm.faces.new([bm.verts[0], bm.verts[1], bm.verts[2], bm.verts[3]])

        # Side faces
        for i in range(4):
            next_i = (i + 1) % 4
            bm.faces.new([
                bm.verts[i],
                bm.verts[4 + i],
                bm.verts[4 + next_i],
                bm.verts[next_i],
            ])

        # Back face
        bm.faces.new([bm.verts[4], bm.verts[7], bm.verts[6], bm.verts[5]])

        bm.to_mesh(mesh)
        bm.free()

        mat = self._get_headlight_material()
        if mat:
            obj.data.materials.append(mat)

        return obj

    def _create_taillight(
        self,
        dims: CarDimensions,
        name: str,
    ) -> Optional[Object]:
        """Create taillight mesh."""
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        bm = bmesh.new()

        # Simple taillight shape (elongated)
        w, h = 0.12, 0.04

        bm.verts.new((-0.05, -w, -h))
        bm.verts.new((-0.05, w, -h))
        bm.verts.new((-0.05, w, h))
        bm.verts.new((-0.05, -w, h))
        bm.verts.new((0.02, -w * 0.8, -h * 0.8))
        bm.verts.new((0.02, w * 0.8, -h * 0.8))
        bm.verts.new((0.02, w * 0.8, h * 0.8))
        bm.verts.new((0.02, -w * 0.8, h * 0.8))

        bm.verts.ensure_lookup_table()

        bm.faces.new([bm.verts[0], bm.verts[1], bm.verts[2], bm.verts[3]])

        for i in range(4):
            next_i = (i + 1) % 4
            bm.faces.new([
                bm.verts[i],
                bm.verts[4 + i],
                bm.verts[4 + next_i],
                bm.verts[next_i],
            ])

        bm.faces.new([bm.verts[4], bm.verts[7], bm.verts[6], bm.verts[5]])

        bm.to_mesh(mesh)
        bm.free()

        mat = self._get_taillight_material()
        if mat:
            obj.data.materials.append(mat)

        return obj

    def _get_car_paint_material(self, config: CarPaintConfig) -> Optional[Any]:
        """Get or create car paint material."""
        if not BLENDER_AVAILABLE:
            return None

        cache_key = f"paint_{config.base_color}"
        if cache_key in self._material_cache:
            return self._material_cache[cache_key]

        mat = bpy.data.materials.new("Car_Paint")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        # Principled BSDF
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (0, 0)
        bsdf.inputs["Base Color"].default_value = (*config.base_color, 1.0)
        bsdf.inputs["Metallic"].default_value = config.metallic
        bsdf.inputs["Roughness"].default_value = config.roughness

        # Clearcoat
        if hasattr(bsdf.inputs, "Clearcoat"):
            bsdf.inputs["Clearcoat"].default_value = config.clearcoat
            bsdf.inputs["Clearcoat Roughness"].default_value = config.clearcoat_roughness

        # Output
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (200, 0)

        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        self._material_cache[cache_key] = mat
        return mat

    def _get_glass_material(self) -> Optional[Any]:
        """Get or create glass material."""
        if not BLENDER_AVAILABLE:
            return None

        if "glass" in self._material_cache:
            return self._material_cache["glass"]

        mat = bpy.data.materials.new("Car_Glass")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        glass = nodes.new("ShaderNodeBsdfGlass")
        glass.inputs["Color"].default_value = (0.1, 0.15, 0.2, 1.0)
        glass.inputs["Roughness"].default_value = 0.02
        glass.inputs["IOR"].default_value = 1.5

        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (200, 0)

        links.new(glass.outputs["BSDF"], output.inputs["Surface"])

        self._material_cache["glass"] = mat
        return mat

    def _get_wheel_material(self) -> Optional[Any]:
        """Get or create wheel material."""
        if not BLENDER_AVAILABLE:
            return None

        if "wheel" in self._material_cache:
            return self._material_cache["wheel"]

        mat = bpy.data.materials.new("Car_Wheel")
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.15, 0.15, 0.15, 1.0)
            bsdf.inputs["Metallic"].default_value = 0.9
            bsdf.inputs["Roughness"].default_value = 0.3

        self._material_cache["wheel"] = mat
        return mat

    def _get_headlight_material(self) -> Optional[Any]:
        """Get or create headlight material."""
        if not BLENDER_AVAILABLE:
            return None

        if "headlight" in self._material_cache:
            return self._material_cache["headlight"]

        mat = bpy.data.materials.new("Car_Headlight")
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
            bsdf.inputs["Emission Color"].default_value = (1.0, 1.0, 0.95, 1.0)
            bsdf.inputs["Emission Strength"].default_value = 5.0

        self._material_cache["headlight"] = mat
        return mat

    def _get_taillight_material(self) -> Optional[Any]:
        """Get or create taillight material."""
        if not BLENDER_AVAILABLE:
            return None

        if "taillight" in self._material_cache:
            return self._material_cache["taillight"]

        mat = bpy.data.materials.new("Car_Taillight")
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.8, 0.1, 0.1, 1.0)
            bsdf.inputs["Emission Color"].default_value = (1.0, 0.1, 0.1, 1.0)
            bsdf.inputs["Emission Strength"].default_value = 3.0

        self._material_cache["taillight"] = mat
        return mat


def create_hero_car(
    car_type: CarType = CarType.SEDAN,
    paint_color: str = "midnight_blue",
    name: str = "Hero_Car",
    collection: Optional[Collection] = None,
) -> Optional[Object]:
    """
    Create a hero car model.

    Args:
        car_type: Type of vehicle
        paint_color: Paint preset name
        name: Object name
        collection: Collection to add to

    Returns:
        Blender object
    """
    builder = HeroCarBuilder()
    paint = PAINT_PRESETS.get(paint_color, PAINT_PRESETS["midnight_blue"])

    car = builder.create_car(car_type, paint_config=paint, name=name)

    if car and collection:
        collection.objects.link(car)

    return car


__all__ = [
    "CarType",
    "CarDimensions",
    "CarPaintConfig",
    "CAR_DIMENSIONS",
    "PAINT_PRESETS",
    "HeroCarBuilder",
    "create_hero_car",
]
