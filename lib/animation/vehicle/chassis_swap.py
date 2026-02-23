"""
Chassis Swap System - Put Any Body on Any Chassis

Allows swapping any car body onto different chassis types:
stock → lifted → monster → baja → lowrider

Usage:
    from lib.animation.vehicle.chassis_swap import (
        ChassisSwapper, ChassisConfig, swap_chassis
    )

    # Swap sedan body onto monster truck chassis
    swapper = ChassisSwapper()
    monster = swapper.swap_chassis(vehicle, "monster")

    # Or create with custom config
    config = ChassisConfig(
        ride_height=0.6,
        suspension_travel=0.4,
        tire_size=0.85
    )
    result = swapper.apply_chassis(vehicle, config)
"""

import bpy
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from math import pi, sin, cos
from mathutils import Vector, Matrix
from enum import Enum


class ChassisType(Enum):
    STOCK = "stock"
    LOWERED = "lowered"
    LIFTED = "lifted"
    BAJA = "baja"
    MONSTER = "monster"
    LOWRIDER = "lowrider"
    PRERUNNER = "prerunner"
    RATROD = "ratrod"


@dataclass
class ChassisConfig:
    """Configuration for a vehicle chassis."""

    # === DIMENSIONS ===
    ride_height: float = 0.15           # Ground clearance (meters)
    wheelbase: float = 2.7              # Front to rear axle (meters)
    track_width_front: float = 1.55     # Front wheel track (meters)
    track_width_rear: float = 1.52      # Rear wheel track (meters)

    # === SUSPENSION ===
    suspension_travel: float = 0.15     # Total travel (meters)
    suspension_type: str = "independent"
    spring_rate: float = 35000.0        # N/m
    damping: float = 4000.0             # Ns/m

    # === TIRES ===
    tire_radius: float = 0.32           # meters
    tire_width: float = 0.225           # meters
    tire_offset: float = 0.0            # Wheel offset

    # === CHASSIS ===
    frame_style: str = "unibody"        # unibody, body_on_frame, tube
    frame_visible: bool = False

    # === WHEEL POSITION ===
    wheel_positions: List[Tuple[float, float, float]] = field(default_factory=lambda: [
        (1.35, 0.8, 0.0),    # FL
        (1.35, -0.8, 0.0),   # FR
        (-1.35, 0.8, 0.0),   # RL
        (-1.35, -0.8, 0.0),  # RR
    ])

    @property
    def wheel_count(self) -> int:
        return len(self.wheel_positions)


# === CHASSIS PRESETS ===

CHASSIS_PRESETS = {
    "stock": ChassisConfig(
        ride_height=0.15,
        suspension_travel=0.15,
        tire_radius=0.32,
        tire_width=0.225,
        frame_style="unibody"
    ),

    "lowered": ChassisConfig(
        ride_height=0.08,
        suspension_travel=0.10,
        tire_radius=0.28,
        tire_width=0.245,
        spring_rate=45000.0,
        frame_style="unibody"
    ),

    "lifted": ChassisConfig(
        ride_height=0.30,
        suspension_travel=0.20,
        tire_radius=0.40,
        tire_width=0.265,
        frame_style="body_on_frame",
        frame_visible=True
    ),

    "baja": ChassisConfig(
        ride_height=0.35,
        suspension_travel=0.35,
        tire_radius=0.45,
        tire_width=0.30,
        spring_rate=28000.0,
        damping=6000.0,
        frame_style="tube",
        frame_visible=True
    ),

    "monster": ChassisConfig(
        ride_height=0.60,
        suspension_travel=0.40,
        tire_radius=0.85,
        tire_width=0.45,
        spring_rate=80000.0,
        damping=12000.0,
        wheelbase=3.8,
        track_width_front=2.5,
        track_width_rear=2.5,
        frame_style="tube",
        frame_visible=True,
        wheel_positions=[
            (1.9, 1.25, 0.0),    # FL - wider
            (1.9, -1.25, 0.0),   # FR
            (-1.9, 1.25, 0.0),   # RL
            (-1.9, -1.25, 0.0),  # RR
        ]
    ),

    "lowrider": ChassisConfig(
        ride_height=0.05,
        suspension_travel=0.20,  # Can go UP as well as down
        tire_radius=0.30,
        tire_width=0.215,
        spring_rate=25000.0,
        frame_style="body_on_frame"
    ),

    "prerunner": ChassisConfig(
        ride_height=0.40,
        suspension_travel=0.50,
        tire_radius=0.42,
        tire_width=0.35,
        spring_rate=30000.0,
        damping=8000.0,
        frame_style="tube",
        frame_visible=True
    ),

    "ratrod": ChassisConfig(
        ride_height=0.12,
        suspension_travel=0.15,
        tire_radius=0.35,  # Bigger rears (using average for simplicity)
        tire_width=0.255,
        frame_style="body_on_frame",
        frame_visible=True
    ),
}


class ChassisSwapper:
    """
    Swap any car body onto different chassis.

    Process:
    1. Store body geometry
    2. Remove existing chassis/suspension
    3. Create new chassis
    4. Reattach body at new height
    5. Update wheel positions
    6. Recalibrate physics
    """

    def __init__(self):
        self.original_configs: Dict[str, Dict] = {}

    def swap_chassis(
        self,
        vehicle: bpy.types.Object,
        chassis_type: str
    ) -> bpy.types.Object:
        """
        Swap vehicle to a different chassis type.

        Args:
            vehicle: The vehicle object
            chassis_type: Preset name (stock, lifted, monster, etc.)

        Returns:
            The modified vehicle
        """
        config = CHASSIS_PRESETS.get(chassis_type, CHASSIS_PRESETS["stock"])
        return self.apply_chassis(vehicle, config, chassis_type)

    def apply_chassis(
        self,
        vehicle: bpy.types.Object,
        config: ChassisConfig,
        chassis_name: str = "custom"
    ) -> bpy.types.Object:
        """
        Apply a custom chassis configuration.

        Args:
            vehicle: The vehicle object
            config: Chassis configuration
            chassis_name: Name for the chassis type

        Returns:
            The modified vehicle
        """
        # Store original configuration for potential revert
        self._store_original_config(vehicle)

        # Get body mesh
        body = self._extract_body(vehicle)
        if not body:
            return vehicle

        # Remove existing chassis components
        self._remove_existing_chassis(vehicle)

        # Create new chassis
        chassis = self._create_chassis(vehicle, config)

        # Position body on new chassis
        self._position_body(body, config)

        # Create wheel assemblies
        wheels = self._create_wheel_assemblies(vehicle, config)

        # Create suspension
        suspension = self._create_suspension(vehicle, config, wheels)

        # Update physics
        self._update_physics(vehicle, config)

        # Store new config
        vehicle["chassis_type"] = chassis_name
        vehicle["chassis_config"] = {
            'ride_height': config.ride_height,
            'wheelbase': config.wheelbase,
            'tire_radius': config.tire_radius,
            'suspension_travel': config.suspension_travel
        }

        return vehicle

    def _store_original_config(self, vehicle: bpy.types.Object) -> None:
        """Store original vehicle configuration for revert."""
        self.original_configs[vehicle.name] = {
            'location': tuple(vehicle.location),
            'rotation': tuple(vehicle.rotation_euler),
            'chassis_type': vehicle.get("chassis_type", "stock")
        }

    def _extract_body(self, vehicle: bpy.types.Object) -> Optional[bpy.types.Object]:
        """Extract the body mesh from vehicle."""
        # Find the body mesh (could be the vehicle itself or a child)
        if vehicle.type == 'MESH':
            return vehicle

        # Look for body child
        for child in vehicle.children:
            if 'body' in child.name.lower() or child.type == 'MESH':
                return child

        return None

    def _remove_existing_chassis(self, vehicle: bpy.types.Object) -> None:
        """Remove existing chassis components."""
        # Remove chassis-related children
        to_remove = []

        for child in vehicle.children:
            name_lower = child.name.lower()
            if any(x in name_lower for x in ['chassis', 'suspension', 'wheel', 'tire', 'frame']):
                to_remove.append(child)

        for obj in to_remove:
            bpy.data.objects.remove(obj, do_unlink=True)

    def _create_chassis(
        self,
        vehicle: bpy.types.Object,
        config: ChassisConfig
    ) -> bpy.types.Object:
        """Create new chassis frame."""
        chassis_name = f"{vehicle.name}_chassis"

        if config.frame_style == "tube" and config.frame_visible:
            return self._create_tube_frame(vehicle, config)
        elif config.frame_style == "body_on_frame" and config.frame_visible:
            return self._create_ladder_frame(vehicle, config)
        else:
            # Unibody - no visible frame
            return vehicle

    def _create_tube_frame(
        self,
        vehicle: bpy.types.Object,
        config: ChassisConfig
    ) -> bpy.types.Object:
        """Create tube chassis frame."""
        chassis_name = f"{vehicle.name}_chassis_tube"

        mesh = bpy.data.meshes.new(f"{chassis_name}_mesh")
        chassis = bpy.data.objects.new(chassis_name, mesh)

        import bmesh
        bm = bmesh.new()

        wb = config.wheelbase
        tw = config.track_width_front

        # Main rails
        rail_y = tw / 2 - 0.2

        # Create tube vertices
        # Left rail
        bm.verts.new((wb/2, rail_y, 0))
        bm.verts.new((-wb/2, rail_y, 0))
        bm.verts.new((wb/2, rail_y, 0.3))
        bm.verts.new((-wb/2, rail_y, 0.3))

        # Right rail
        bm.verts.new((wb/2, -rail_y, 0))
        bm.verts.new((-wb/2, -rail_y, 0))
        bm.verts.new((wb/2, -rail_y, 0.3))
        bm.verts.new((-wb/2, -rail_y, 0.3))

        # Cross bars
        bm.verts.new((wb/2, rail_y, 0.3))
        bm.verts.new((wb/2, -rail_y, 0.3))
        bm.verts.new((0, rail_y, 0.3))
        bm.verts.new((0, -rail_y, 0.3))
        bm.verts.new((-wb/2, rail_y, 0.3))
        bm.verts.new((-wb/2, -rail_y, 0.3))

        # Roll cage (for baja/prerunner)
        bm.verts.new((wb/4, rail_y, 1.0))
        bm.verts.new((wb/4, -rail_y, 1.0))
        bm.verts.new((-wb/4, rail_y, 1.0))
        bm.verts.new((-wb/4, -rail_y, 1.0))

        bm.verts.ensure_lookup_table()
        bm.to_mesh(mesh)
        bm.free()

        chassis.location = vehicle.location
        chassis.location.z = config.ride_height
        chassis.parent = vehicle
        bpy.context.collection.objects.link(chassis)

        return chassis

    def _create_ladder_frame(
        self,
        vehicle: bpy.types.Object,
        config: ChassisConfig
    ) -> bpy.types.Object:
        """Create ladder frame chassis."""
        chassis_name = f"{vehicle.name}_chassis_ladder"

        bpy.ops.mesh.primitive_cube_add(size=1)
        chassis = bpy.context.active_object
        chassis.name = chassis_name

        wb = config.wheelbase
        tw = config.track_width_front

        chassis.scale = (wb * 1.1, 0.15, 0.08)
        chassis.location = vehicle.location
        chassis.location.z = config.ride_height / 2
        chassis.parent = vehicle

        # Create second rail
        bpy.ops.mesh.primitive_cube_add(size=1)
        rail = bpy.context.active_object
        rail.name = f"{chassis_name}_rail"
        rail.scale = (wb * 1.1, 0.15, 0.08)
        rail.location = (vehicle.location.x, vehicle.location.y + tw/2 - 0.1, config.ride_height/2)
        rail.parent = vehicle

        # Third rail (opposite side)
        bpy.ops.mesh.primitive_cube_add(size=1)
        rail2 = bpy.context.active_object
        rail2.name = f"{chassis_name}_rail2"
        rail2.scale = (wb * 1.1, 0.15, 0.08)
        rail2.location = (vehicle.location.x, vehicle.location.y - tw/2 + 0.1, config.ride_height/2)
        rail2.parent = vehicle

        return chassis

    def _position_body(
        self,
        body: bpy.types.Object,
        config: ChassisConfig
    ) -> None:
        """Position body on new chassis."""
        # Adjust body height to match ride height
        if body.type == 'MESH':
            # Get bounding box
            bbox = body.bound_box
            min_z = min(v[2] for v in bbox)

            # Offset so bottom of body sits on chassis
            offset = config.ride_height - min_z
            body.location.z += offset

    def _create_wheel_assemblies(
        self,
        vehicle: bpy.types.Object,
        config: ChassisConfig
    ) -> List[bpy.types.Object]:
        """Create wheel assemblies at new positions."""
        wheels = []

        for i, (x, y, z) in enumerate(config.wheel_positions):
            wheel_name = f"{vehicle.name}_wheel_{i}"

            # Create wheel empty
            wheel = bpy.data.objects.new(wheel_name, None)
            wheel.empty_display_type = 'ARROWS'
            wheel.empty_display_size = config.tire_radius

            # Position relative to vehicle
            wheel.location = Vector((x, y, z + config.ride_height))
            wheel.parent = vehicle
            bpy.context.collection.objects.link(wheel)

            # Create tire mesh
            tire = self._create_tire_mesh(config.tire_radius, config.tire_width)
            tire.name = f"{wheel_name}_tire"
            tire.parent = wheel

            wheels.append(wheel)

        return wheels

    def _create_tire_mesh(
        self,
        radius: float,
        width: float
    ) -> bpy.types.Object:
        """Create a tire mesh."""
        tire_name = f"tire_{radius:.2f}"

        # Check if we already have this tire
        existing = bpy.data.objects.get(tire_name)
        if existing:
            # Duplicate
            tire = existing.copy()
            tire.data = existing.data.copy()
            bpy.context.collection.objects.link(tire)
            return tire

        # Create torus for tire
        import bmesh
        mesh = bpy.data.meshes.new(f"{tire_name}_mesh")
        tire = bpy.data.objects.new(tire_name, mesh)

        bm = bmesh.new()

        segments = 32
        ring_segments = 12
        tube_radius = width / 2

        for i in range(segments):
            angle = 2 * pi * i / segments
            for j in range(ring_segments):
                ring_angle = 2 * pi * j / ring_segments

                y = (radius + tube_radius * cos(ring_angle)) * cos(angle)
                z = (radius + tube_radius * cos(ring_angle)) * sin(angle) + tube_radius * sin(ring_angle)

                bm.verts.new((0, y, z))

        bm.verts.ensure_lookup_table()

        # Create faces
        for i in range(segments):
            for j in range(ring_segments):
                i1 = i * ring_segments + j
                i2 = i * ring_segments + (j + 1) % ring_segments
                i3 = ((i + 1) % segments) * ring_segments + (j + 1) % ring_segments
                i4 = ((i + 1) % segments) * ring_segments + j

                try:
                    bm.faces.new([
                        bm.verts[i1], bm.verts[i2],
                        bm.verts[i3], bm.verts[i4]
                    ])
                except:
                    pass

        bm.to_mesh(mesh)
        bm.free()

        bpy.context.collection.objects.link(tire)

        return tire

    def _create_suspension(
        self,
        vehicle: bpy.types.Object,
        config: ChassisConfig,
        wheels: List[bpy.types.Object]
    ) -> List[bpy.types.Object]:
        """Create suspension components."""
        from .suspension_physics import SuspensionPhysics, SuspensionSystem, setup_suspension

        susp_config = SuspensionPhysics(
            spring_rate=config.spring_rate,
            damping_coefficient=config.damping,
            travel=config.suspension_travel
        )

        system = SuspensionSystem()

        for i, wheel in enumerate(wheels):
            is_front = i < 2
            system.create_suspension_rig(wheel, susp_config, is_front)

        return wheels

    def _update_physics(
        self,
        vehicle: bpy.types.Object,
        config: ChassisConfig
    ) -> None:
        """Update vehicle physics for new chassis."""
        from .physics_core import PhysicsEngine, VehiclePhysics, DrivetrainType

        # Calculate mass based on chassis type
        base_mass = 1500
        if config.tire_radius > 0.5:  # Monster
            base_mass = 4500
        elif config.tire_radius > 0.35:  # Lifted/Offroad
            base_mass = 2500

        physics = VehiclePhysics(
            mass=base_mass,
            center_of_gravity_height=config.ride_height / 2,
            tire_radius_front=config.tire_radius,
            tire_radius_rear=config.tire_radius,
            wheelbase=config.wheelbase,
            track_width_front=config.track_width_front,
            track_width_rear=config.track_width_rear
        )

        engine = PhysicsEngine()
        engine.setup_rigid_body(vehicle, physics)

    def revert_chassis(self, vehicle: bpy.types.Object) -> bool:
        """
        Revert vehicle to original chassis.

        Returns:
            True if reverted successfully
        """
        original = self.original_configs.get(vehicle.name)
        if not original:
            return False

        # Revert to stock chassis
        self.swap_chassis(vehicle, original.get('chassis_type', 'stock'))

        # Restore original position/rotation
        vehicle.location = Vector(original['location'])
        vehicle.rotation_euler = Euler(original['rotation'])

        return True

    def get_available_chassis_types(self) -> List[str]:
        """Get list of available chassis presets."""
        return list(CHASSIS_PRESETS.keys())

    def get_chassis_config(self, preset_name: str) -> Optional[ChassisConfig]:
        """Get a chassis configuration by preset name."""
        return CHASSIS_PRESETS.get(preset_name)


def swap_chassis(
    vehicle: bpy.types.Object,
    chassis_type: str
) -> bpy.types.Object:
    """
    Convenience function to swap chassis.

    Args:
        vehicle: The vehicle object
        chassis_type: Preset name

    Returns:
        The modified vehicle
    """
    swapper = ChassisSwapper()
    return swapper.swap_chassis(vehicle, chassis_type)


def list_chassis_types() -> List[str]:
    """List available chassis types."""
    return list(CHASSIS_PRESETS.keys())


def get_chassis_config(preset_name: str) -> ChassisConfig:
    """Get a chassis configuration preset."""
    return CHASSIS_PRESETS.get(preset_name, CHASSIS_PRESETS["stock"])
