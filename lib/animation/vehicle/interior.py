"""
Interior System - Procedural Vehicle Interiors

Generates procedural interiors for vehicles with varying detail levels.
From basic silhouettes to full hero car interiors with animated steering.

Usage:
    from lib.animation.vehicle.interior import (
        InteriorConfig, InteriorFactory, create_interior
    )

    # Hero interior (full detail)
    config = InteriorConfig(detail_level="hero")
    interior = InteriorFactory().create_interior(vehicle, config)

    # Connect steering wheel to front tires
    factory.connect_steering_to_wheels(
        steering_wheel=interior['steering_wheel'],
        front_wheels=[wheel_FL, wheel_FR],
        ratio=15.0  # 540° steering = 36° wheel angle
    )
"""

import bpy
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from math import pi, sin, cos
from mathutils import Vector, Matrix
from enum import Enum
import bmesh


class InteriorDetailLevel(Enum):
    NONE = "none"           # No interior (distant background)
    SILHOUETTE = "silhouette"  # Basic shapes visible
    TRAFFIC = "traffic"     # Simplified (background cars)
    FEATURE = "feature"     # Visible through windows
    HERO = "hero"           # Full detail, close-up ready


@dataclass
class InteriorConfig:
    """Configuration for procedural vehicle interior."""

    detail_level: InteriorDetailLevel = InteriorDetailLevel.FEATURE

    # === COMPONENTS ===
    steering_wheel: bool = True
    dashboard: bool = True
    seats: bool = True
    rear_view_mirror: bool = True
    gear_shifter: bool = True
    pedals: bool = False
    instruments: bool = False
    door_panels: bool = False
    roof_liner: bool = False

    # === VISIBILITY ===
    window_tint: float = 0.3        # 0=clear, 1=blackout
    interior_color: Tuple[float, float, float] = (0.15, 0.15, 0.15)  # Dark gray

    # === STEERING ===
    steering_diameter: float = 0.38  # meters
    steering_thickness: float = 0.03
    steering_spokes: int = 3          # 2, 3, or 4
    steering_ratio: float = 15.0      # Steering wheel : wheel angle ratio

    # === SEATS ===
    seat_style: str = "bucket"        # bench, bucket, racing
    seat_color: Tuple[float, float, float] = (0.2, 0.2, 0.25)

    # === DASHBOARD ===
    dashboard_style: str = "modern"   # classic, modern, sport


# === INTERIOR PRESETS ===

INTERIOR_PRESETS = {
    "none": InteriorConfig(
        detail_level=InteriorDetailLevel.NONE
    ),

    "background": InteriorConfig(
        detail_level=InteriorDetailLevel.SILHOUETTE,
        steering_wheel=True,
        dashboard=True,
        seats=True,
        steering_spokes=3
    ),

    "traffic": InteriorConfig(
        detail_level=InteriorDetailLevel.TRAFFIC,
        steering_wheel=True,
        dashboard=True,
        seats=True,
        rear_view_mirror=True,
        window_tint=0.4
    ),

    "feature": InteriorConfig(
        detail_level=InteriorDetailLevel.FEATURE,
        steering_wheel=True,
        dashboard=True,
        seats=True,
        rear_view_mirror=True,
        gear_shifter=True,
        window_tint=0.3
    ),

    "hero": InteriorConfig(
        detail_level=InteriorDetailLevel.HERO,
        steering_wheel=True,
        dashboard=True,
        seats=True,
        rear_view_mirror=True,
        gear_shifter=True,
        pedals=True,
        instruments=True,
        door_panels=True,
        roof_liner=True,
        window_tint=0.2
    ),

    "racing": InteriorConfig(
        detail_level=InteriorDetailLevel.HERO,
        steering_wheel=True,
        dashboard=True,
        seats=True,
        rear_view_mirror=False,  # Often removed in race cars
        gear_shifter=True,
        pedals=True,
        instruments=True,
        seat_style="racing",
        steering_spokes=3,
        steering_diameter=0.35
    ),

    "muscle": InteriorConfig(
        detail_level=InteriorDetailLevel.HERO,
        steering_wheel=True,
        dashboard=True,
        seats=True,
        gear_shifter=True,
        pedals=True,
        seat_style="bucket",
        steering_spokes=2,
        steering_diameter=0.42,
        dashboard_style="classic"
    ),

    "luxury": InteriorConfig(
        detail_level=InteriorDetailLevel.HERO,
        steering_wheel=True,
        dashboard=True,
        seats=True,
        rear_view_mirror=True,
        gear_shifter=True,
        pedals=True,
        instruments=True,
        door_panels=True,
        roof_liner=True,
        seat_style="bucket",
        seat_color=(0.25, 0.22, 0.18),  # Warm leather
        interior_color=(0.2, 0.18, 0.16),
        window_tint=0.15
    ),
}


class InteriorFactory:
    """Factory for creating procedural vehicle interiors."""

    def __init__(self):
        self.components: Dict[str, bpy.types.Object] = {}

    def create_interior(
        self,
        vehicle: bpy.types.Object,
        config: InteriorConfig,
        collection: Optional[bpy.types.Collection] = None
    ) -> Dict[str, Any]:
        """
        Create procedural interior for a vehicle.

        Args:
            vehicle: The vehicle object (for dimensions)
            config: Interior configuration
            collection: Optional collection to parent interior to

        Returns:
            Dictionary with interior component references
        """
        if config.detail_level == InteriorDetailLevel.NONE:
            return {}

        # Get vehicle dimensions
        bbox = self._get_bounding_box(vehicle)
        interior_width = bbox['width'] * 0.85
        interior_length = bbox['length'] * 0.4
        interior_height = bbox['height'] * 0.6

        # Create interior root
        interior_name = f"{vehicle.name}_interior"
        interior_root = bpy.data.objects.new(interior_name, None)
        interior_root.empty_display_type = 'ARROWS'
        interior_root.location = vehicle.location
        interior_root.parent = vehicle

        if collection:
            collection.objects.link(interior_root)
        else:
            bpy.context.collection.objects.link(interior_root)

        result = {'root': interior_root}

        # Create components based on detail level and config
        if config.steering_wheel:
            result['steering_wheel'] = self._create_steering_wheel(
                interior_root, config, interior_width
            )

        if config.dashboard:
            result['dashboard'] = self._create_dashboard(
                interior_root, config, interior_width, interior_length
            )

        if config.seats:
            result['seats'] = self._create_seats(
                interior_root, config, interior_width, interior_length
            )

        if config.rear_view_mirror:
            result['mirror'] = self._create_rear_view_mirror(
                interior_root, config, interior_width
            )

        if config.gear_shifter:
            result['shifter'] = self._create_gear_shifter(
                interior_root, config
            )

        if config.pedals:
            result['pedals'] = self._create_pedals(
                interior_root, config
            )

        if config.instruments and config.detail_level == InteriorDetailLevel.HERO:
            result['instruments'] = self._create_instruments(
                interior_root, config, interior_width
            )

        self.components = result
        return result

    def connect_steering_to_wheels(
        self,
        steering_wheel: bpy.types.Object,
        front_wheels: List[bpy.types.Object],
        ratio: float = 15.0
    ) -> None:
        """
        Connect steering wheel rotation to front wheel steering.

        Creates driver constraint: steering wheel Y rotation -> wheel Z rotation

        Args:
            steering_wheel: Steering wheel object
            front_wheels: [FL, FR] wheel pivot objects
            ratio: Steering ratio (540° wheel = 36° tire means 15:1)
        """
        for wheel in front_wheels:
            if wheel is None:
                continue

            # Add driver to wheel's Z rotation (steering)
            fcurve = wheel.driver_add("rotation_euler", 2)
            driver = fcurve.driver

            # Add variable for steering wheel rotation
            var = driver.variables.new()
            var.name = "steer"
            var.targets[0].id_type = 'OBJECT'
            var.targets[0].id = steering_wheel
            var.targets[0].data_path = "rotation_euler[1]"  # Y rotation

            # Expression: divide by ratio to get wheel angle
            # Negative because steering wheel rotation is opposite to wheel
            driver.expression = f"-steer / {ratio}"

    def add_path_based_steering(
        self,
        steering_wheel: bpy.types.Object,
        path_curve: bpy.types.Curve,
        look_ahead: float = 5.0,
        sensitivity: float = 1.0
    ) -> None:
        """
        Add automatic steering based on path curvature.

        The steering wheel will turn based on upcoming path direction.

        Args:
            steering_wheel: Steering wheel object
            path_curve: The path the vehicle follows
            look_ahead: How far ahead to look (in path units)
            sensitivity: How responsive the steering is
        """
        # Add driver to steering wheel rotation
        fcurve = steering_wheel.driver_add("rotation_euler", 1)  # Y rotation
        driver = fcurve.driver

        # This would need a custom driver function in practice
        # For now, set up a simple variable-based driver
        var = driver.variables.new()
        var.name = "path_factor"
        var.targets[0].id_type = 'OBJECT'
        var.targets[0].id = path_curve
        var.targets[0].data_path = "evaluated_path_factor"  # Hypothetical

        # Expression for steering based on path
        driver.expression = f"path_factor * {sensitivity}"

    def _create_steering_wheel(
        self,
        parent: bpy.types.Object,
        config: InteriorConfig,
        interior_width: float
    ) -> bpy.types.Object:
        """Create steering wheel mesh and rig."""
        diameter = config.steering_diameter
        thickness = config.steering_thickness
        spokes = config.steering_spokes

        # Create steering wheel empty (pivot)
        wheel_name = f"{parent.name}_steering"
        wheel_empty = bpy.data.objects.new(wheel_name, None)
        wheel_empty.empty_display_type = 'ARROWS'

        # Position: driver's position, angled
        wheel_empty.location = (0.8, -interior_width/4, 0.9)
        wheel_empty.rotation_euler = (pi/6, 0, 0)  # Tilted back
        wheel_empty.parent = parent
        bpy.context.collection.objects.link(wheel_empty)

        # Create steering wheel mesh (torus + spokes)
        mesh = bpy.data.meshes.new(f"{wheel_name}_mesh")
        wheel_obj = bpy.data.objects.new(wheel_name, mesh)

        # Create torus for rim
        bm = bmesh.new()

        # Rim (torus)
        segments = 32
        ring_segments = 8
        for i in range(segments):
            angle = 2 * pi * i / segments
            for j in range(ring_segments):
                ring_angle = 2 * pi * j / ring_segments

                # Position on torus
                x = (diameter/2 + thickness * cos(ring_angle)) * cos(angle)
                y = (diameter/2 + thickness * cos(ring_angle)) * sin(angle)
                z = thickness * sin(ring_angle)

                bm.verts.new((x, y, z))

        bm.verts.ensure_lookup_table()

        # Create faces (simplified - just the rim)
        for i in range(segments):
            for j in range(ring_segments):
                v1 = bm.verts[i * ring_segments + j]
                v2 = bm.verts[i * ring_segments + (j + 1) % ring_segments]
                v3 = bm.verts[((i + 1) % segments) * ring_segments + (j + 1) % ring_segments]
                v4 = bm.verts[((i + 1) % segments) * ring_segments + j]
                bm.faces.new([v1, v2, v3, v4])

        # Create spokes
        for s in range(spokes):
            spoke_angle = 2 * pi * s / spokes
            # Create spoke vertices
            v_center = bm.verts.new((0, 0, 0))
            v_outer = bm.verts.new((
                diameter/2 * cos(spoke_angle),
                diameter/2 * sin(spoke_angle),
                0
            ))

        bm.to_mesh(mesh)
        bm.free()

        # Position wheel mesh
        wheel_obj.location = (0, 0, 0)
        wheel_obj.parent = wheel_empty
        bpy.context.collection.objects.link(wheel_obj)

        # Create material
        mat = self._create_interior_material("steering_wheel", (0.2, 0.2, 0.2), roughness=0.8)
        if wheel_obj.data.materials:
            wheel_obj.data.materials[0] = mat
        else:
            wheel_obj.data.materials.append(mat)

        return wheel_empty

    def _create_dashboard(
        self,
        parent: bpy.types.Object,
        config: InteriorConfig,
        interior_width: float,
        interior_length: float
    ) -> bpy.types.Object:
        """Create dashboard mesh."""
        dash_name = f"{parent.name}_dashboard"

        # Create dashboard mesh
        mesh = bpy.data.meshes.new(f"{dash_name}_mesh")
        dash_obj = bpy.data.objects.new(dash_name, mesh)

        # Create simple dashboard shape
        bm = bmesh.new()

        # Dashboard vertices (simplified box with curved top)
        w = interior_width / 2
        d = interior_length / 3
        h = 0.25

        # Bottom
        v1 = bm.verts.new((0.5, -w, 0.6))
        v2 = bm.verts.new((0.5, w, 0.6))
        v3 = bm.verts.new((0.5 + d, w, 0.6))
        v4 = bm.verts.new((0.5 + d, -w, 0.6))

        # Top (curved up slightly)
        v5 = bm.verts.new((0.5, -w, 0.85))
        v6 = bm.verts.new((0.5, w, 0.85))
        v7 = bm.verts.new((0.5 + d, w, 0.8))
        v8 = bm.verts.new((0.5 + d, -w, 0.8))

        # Front face
        bm.faces.new([v1, v2, v6, v5])
        # Top face
        bm.faces.new([v5, v6, v7, v8])
        # Back face
        bm.faces.new([v3, v4, v8, v7])
        # Bottom face
        bm.faces.new([v1, v4, v3, v2])

        bm.to_mesh(mesh)
        bm.free()

        dash_obj.parent = parent
        bpy.context.collection.objects.link(dash_obj)

        # Create material
        mat = self._create_interior_material("dashboard", config.interior_color)
        dash_obj.data.materials.append(mat)

        return dash_obj

    def _create_seats(
        self,
        parent: bpy.types.Object,
        config: InteriorConfig,
        interior_width: float,
        interior_length: float
    ) -> List[bpy.types.Object]:
        """Create front seats."""
        seats = []

        for side in ['left', 'right']:
            seat_name = f"{parent.name}_seat_{side}"

            # Create seat mesh
            mesh = bpy.data.meshes.new(f"{seat_name}_mesh")
            seat_obj = bpy.data.objects.new(seat_name, mesh)

            # Create seat shape based on style
            bm = bmesh.new()

            y_offset = interior_width/4 if side == 'left' else -interior_width/4

            # Seat base
            if config.seat_style == "racing":
                # Bucket seat with high sides
                v1 = bm.verts.new((0.3, y_offset - 0.25, 0.3))
                v2 = bm.verts.new((0.3, y_offset + 0.25, 0.3))
                v3 = bm.verts.new((0.8, y_offset + 0.25, 0.3))
                v4 = bm.verts.new((0.8, y_offset - 0.25, 0.3))

                # Seat back (high)
                v5 = bm.verts.new((0.3, y_offset - 0.25, 0.9))
                v6 = bm.verts.new((0.3, y_offset + 0.25, 0.9))
                v7 = bm.verts.new((0.1, y_offset + 0.25, 1.1))
                v8 = bm.verts.new((0.1, y_offset - 0.25, 1.1))
            else:
                # Standard seat
                v1 = bm.verts.new((0.3, y_offset - 0.22, 0.3))
                v2 = bm.verts.new((0.3, y_offset + 0.22, 0.3))
                v3 = bm.verts.new((0.8, y_offset + 0.22, 0.3))
                v4 = bm.verts.new((0.8, y_offset - 0.22, 0.3))

                v5 = bm.verts.new((0.3, y_offset - 0.22, 0.7))
                v6 = bm.verts.new((0.3, y_offset + 0.22, 0.7))
                v7 = bm.verts.new((0.15, y_offset + 0.22, 0.95))
                v8 = bm.verts.new((0.15, y_offset - 0.22, 0.95))

            # Create faces
            bm.faces.new([v1, v2, v6, v5])  # Front
            bm.faces.new([v5, v6, v7, v8])  # Back
            bm.faces.new([v1, v4, v3, v2])  # Bottom
            bm.faces.new([v1, v5, v8, v4])  # Left
            bm.faces.new([v2, v3, v7, v6])  # Right

            bm.to_mesh(mesh)
            bm.free()

            seat_obj.parent = parent
            bpy.context.collection.objects.link(seat_obj)

            # Create material
            mat = self._create_interior_material(f"seat_{side}", config.seat_color, roughness=0.9)
            seat_obj.data.materials.append(mat)

            seats.append(seat_obj)

        return seats

    def _create_rear_view_mirror(
        self,
        parent: bpy.types.Object,
        config: InteriorConfig,
        interior_width: float
    ) -> bpy.types.Object:
        """Create rear view mirror."""
        mirror_name = f"{parent.name}_mirror"

        # Create mirror mesh
        mesh = bpy.data.meshes.new(f"{mirror_name}_mesh")
        mirror_obj = bpy.data.objects.new(mirror_name, mesh)

        bm = bmesh.new()

        # Simple rectangular mirror
        w, h, d = 0.12, 0.05, 0.02
        vertices = [
            (-w, -h, -d), (w, -h, -d), (w, h, -d), (-w, h, -d),
            (-w, -h, d), (w, -h, d), (w, h, d), (-w, h, d)
        ]

        verts = [bm.verts.new(v) for v in vertices]

        # Faces
        bm.faces.new([verts[0], verts[1], verts[2], verts[3]])  # Front
        bm.faces.new([verts[4], verts[7], verts[6], verts[5]])  # Back
        bm.faces.new([verts[0], verts[4], verts[5], verts[1]])  # Bottom
        bm.faces.new([verts[2], verts[6], verts[7], verts[3]])  # Top
        bm.faces.new([verts[0], verts[3], verts[7], verts[4]])  # Left
        bm.faces.new([verts[1], verts[5], verts[6], verts[2]])  # Right

        bm.to_mesh(mesh)
        bm.free()

        # Position at top of windshield
        mirror_obj.location = (0.2, 0, 1.3)
        mirror_obj.rotation_euler = (pi/8, 0, 0)
        mirror_obj.parent = parent
        bpy.context.collection.objects.link(mirror_obj)

        # Mirror material
        mat = self._create_interior_material("mirror", (0.8, 0.8, 0.85), metalness=0.9, roughness=0.1)
        mirror_obj.data.materials.append(mat)

        return mirror_obj

    def _create_gear_shifter(
        self,
        parent: bpy.types.Object,
        config: InteriorConfig
    ) -> bpy.types.Object:
        """Create gear shifter."""
        shifter_name = f"{parent.name}_shifter"

        # Create shifter empty
        shifter_empty = bpy.data.objects.new(shifter_name, None)
        shifter_empty.empty_display_type = 'ARROWS'
        shifter_empty.location = (0.3, 0.1, 0.65)
        shifter_empty.parent = parent
        bpy.context.collection.objects.link(shifter_empty)

        # Create shifter knob
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.025, location=(0.3, 0.1, 0.72))
        knob = bpy.context.active_object
        knob.name = f"{shifter_name}_knob"
        knob.parent = parent

        # Create shifter shaft
        bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.07, location=(0.3, 0.1, 0.68))
        shaft = bpy.context.active_object
        shaft.name = f"{shifter_name}_shaft"
        shaft.parent = parent

        # Material
        mat = self._create_interior_material("shifter", (0.15, 0.15, 0.15), roughness=0.7)
        knob.data.materials.append(mat)
        shaft.data.materials.append(mat)

        return shifter_empty

    def _create_pedals(
        self,
        parent: bpy.types.Object,
        config: InteriorConfig
    ) -> List[bpy.types.Object]:
        """Create accelerator, brake, and clutch pedals."""
        pedals = []
        pedal_names = ['clutch', 'brake', 'accel']

        for i, name in enumerate(pedal_names):
            pedal_name = f"{parent.name}_pedal_{name}"

            # Create pedal mesh
            mesh = bpy.data.meshes.new(f"{pedal_name}_mesh")
            pedal_obj = bpy.data.objects.new(pedal_name, mesh)

            bm = bmesh.new()

            # Simple pedal shape
            w, h, d = 0.05, 0.1, 0.01
            y_offset = 0.2 - i * 0.12  # Spaced left to right (LHD)

            vertices = [
                (-w, y_offset - d, 0.25), (w, y_offset - d, 0.25),
                (w, y_offset - d, 0.35), (-w, y_offset - d, 0.35),
                (-w, y_offset + d, 0.27), (w, y_offset + d, 0.27),
                (w, y_offset + d, 0.37), (-w, y_offset + d, 0.37)
            ]

            verts = [bm.verts.new(v) for v in vertices]

            # Create faces
            bm.faces.new([verts[0], verts[1], verts[2], verts[3]])
            bm.faces.new([verts[4], verts[7], verts[6], verts[5]])
            bm.faces.new([verts[0], verts[4], verts[5], verts[1]])
            bm.faces.new([verts[2], verts[6], verts[7], verts[3]])

            bm.to_mesh(mesh)
            bm.free()

            pedal_obj.parent = parent
            bpy.context.collection.objects.link(pedal_obj)

            # Material (brake is red, others are black)
            if name == 'brake':
                mat = self._create_interior_material("pedal_brake", (0.6, 0.1, 0.1))
            else:
                mat = self._create_interior_material("pedal", (0.1, 0.1, 0.1), metalness=0.5)
            pedal_obj.data.materials.append(mat)

            pedals.append(pedal_obj)

        return pedals

    def _create_instruments(
        self,
        parent: bpy.types.Object,
        config: InteriorConfig,
        interior_width: float
    ) -> bpy.types.Object:
        """Create instrument cluster (speedometer, tachometer)."""
        cluster_name = f"{parent.name}_instruments"

        # Create cluster empty
        cluster = bpy.data.objects.new(cluster_name, None)
        cluster.empty_display_type = 'CUBE'
        cluster.empty_display_size = 0.1
        cluster.location = (0.55, 0, 0.85)
        cluster.parent = parent
        bpy.context.collection.objects.link(cluster)

        # Create gauge faces (simplified circles)
        for i, gauge in enumerate(['speedo', 'tach']):
            gauge_name = f"{cluster_name}_{gauge}"
            x_offset = 0.15 if gauge == 'speedo' else -0.15

            bpy.ops.mesh.primitive_circle_add(radius=0.06, location=(0.55 + x_offset, 0, 0.85))
            gauge_obj = bpy.context.active_object
            gauge_obj.name = gauge_name
            gauge_obj.parent = parent

            # Fill the circle
            bm = bmesh.new()
            bmesh.ops.create_circle(bm, radius=0.06, segments=32)
            bm.to_mesh(gauge_obj.data)
            bm.free()

            # Gauge material (dark background)
            mat = self._create_interior_material(gauge, (0.05, 0.05, 0.08), emission=0.1)
            gauge_obj.data.materials.append(mat)

        return cluster

    def _create_interior_material(
        self,
        name: str,
        color: Tuple[float, float, float],
        roughness: float = 0.8,
        metalness: float = 0.0,
        emission: float = 0.0
    ) -> bpy.types.Material:
        """Create a material for interior components."""
        mat_name = f"interior_{name}"

        if mat_name in bpy.data.materials:
            return bpy.data.materials[mat_name]

        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*color, 1.0)
            bsdf.inputs["Roughness"].default_value = roughness
            bsdf.inputs["Metallic"].default_value = metalness
            if emission > 0:
                bsdf.inputs["Emission"].default_value = (*color, emission)
                bsdf.inputs["Emission Strength"].default_value = emission

        return mat

    def _get_bounding_box(self, obj: bpy.types.Object) -> Dict[str, float]:
        """Get bounding box dimensions."""
        bbox = obj.bound_box
        min_x = min(v[0] for v in bbox)
        max_x = max(v[0] for v in bbox)
        min_y = min(v[1] for v in bbox)
        max_y = max(v[1] for v in bbox)
        min_z = min(v[2] for v in bbox)
        max_z = max(v[2] for v in bbox)

        return {
            'length': max_x - min_x,
            'width': max_y - min_y,
            'height': max_z - min_z,
            'min': Vector((min_x, min_y, min_z)),
            'max': Vector((max_x, max_y, max_z))
        }


# === CONVENIENCE FUNCTIONS ===

def create_interior(
    vehicle: bpy.types.Object,
    preset: str = "feature",
    custom_config: Optional[InteriorConfig] = None
) -> Dict[str, Any]:
    """
    Convenience function to create vehicle interior.

    Args:
        vehicle: The vehicle object
        preset: Interior preset name
        custom_config: Override with custom config

    Returns:
        Dictionary with interior components
    """
    config = custom_config or INTERIOR_PRESETS.get(preset, INTERIOR_PRESETS["feature"])
    factory = InteriorFactory()
    return factory.create_interior(vehicle, config)


def get_interior_preset(preset_name: str) -> InteriorConfig:
    """Get an interior preset by name."""
    return INTERIOR_PRESETS.get(preset_name, INTERIOR_PRESETS["feature"])


def list_interior_presets() -> List[str]:
    """List available interior presets."""
    return list(INTERIOR_PRESETS.keys())
