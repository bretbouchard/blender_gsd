"""
Monster Factory - Mad Max Style Mutant Vehicles

Creates extreme wasteland vehicles with monster truck chassis,
armor plating, oversized tires, and improvised modifications.

Usage:
    from lib.animation.vehicle.monster_factory import (
        MonsterConfig, MonsterFactory, create_monster_car
    )

    # Create a monster version of any car
    monster = create_monster_car(
        base_style="sedan",
        config=MonsterConfig(
            chassis_type="monster",
            lift_height=0.6,
            armor_plating=True,
            spikes=True
        )
    )
"""

import bpy
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from math import pi, sin, cos, random
from mathutils import Vector, Matrix, Euler
from enum import Enum
import random


class ChassisType(Enum):
    STOCK = "stock"             # Standard ride height
    LOWERED = "lowered"         # Lowrider style
    LIFTED = "lifted"           # Mild lift (2-4")
    PRERUNNER = "prerunner"     # Baja style
    MONSTER = "monster"         # Full monster truck
    APOCALYPSE = "apocalypse"   # Max Mad extreme


class TireSize(Enum):
    STOCK = "stock"             # Standard
    LOW_PROFILE = "low_profile" # Sport
    ALL_TERRAIN = "all_terrain" # Mild offroad
    MUD_TERRAIN = "mud_terrain" # Aggressive
    BOGGER = "bogger"           # Super swampers
    MONSTER = "monster"         # 66" tires


class ArmorStyle(Enum):
    NONE = "none"
    SCRAP = "scrap"             # Random metal plates
    INDUSTRIAL = "industrial"   # Welded steel
    MILITARY = "military"       # Armored plates
    SPIKED = "spiked"           # Spikes everywhere


@dataclass
class MonsterConfig:
    """Configuration for mutant/monster vehicles."""

    # === CHASSIS ===
    chassis_type: ChassisType = ChassisType.MONSTER
    lift_height: float = 0.0            # Additional lift in meters
    chassis_visible: bool = True        # Show tube chassis

    # === TIRES ===
    tire_size: TireSize = TireSize.MONSTER
    tire_size_multiplier: float = 1.0
    tire_wobble: float = 0.0            # Low speed tire shake

    # === ARMOR ===
    armor_plating: bool = True
    armor_style: ArmorStyle = ArmorStyle.SCRAP
    armor_coverage: float = 0.5         # 0-1 how much is covered

    # === WEAPONS (Visual) ===
    ram_bars: bool = False
    ram_bar_style: str = "push"         # push, spike, blade
    spinning_blades: bool = False
    flamethrower: bool = False
    harpoon: bool = False
    guns_mounted: bool = False

    # === SPIKES ===
    spikes: bool = False
    spike_count: int = 20
    spike_length: float = 0.2

    # === IMPROVISED REPAIRS ===
    improvised_repairs: bool = True
    duct_tape_patches: int = 5
    wire_repairs: int = 3
    cardboard_windows: bool = False

    # === SCRAP ===
    scrap_armor: bool = True
    door_mismatch: bool = False         # Different colored doors
    hood_scoops: bool = False
    exhaust_stacks: bool = False

    # === WEATHERING ===
    rust_level: float = 0.5
    battle_damage: float = 0.3
    blood_splatter: float = 0.0         # For... atmosphere

    # === ACCESSORIES ===
    skull_decorations: bool = False
    chains: bool = False
    barbed_wire: bool = False
    lights_extra: bool = False
    fuel_tanks: bool = False
    storage_cages: bool = False


# === MONSTER PRESETS ===

MONSTER_PRESETS = {
    "stock": MonsterConfig(
        chassis_type=ChassisType.STOCK,
        armor_plating=False,
        improvised_repairs=False
    ),

    "lifted": MonsterConfig(
        chassis_type=ChassisType.LIFTED,
        lift_height=0.15,
        tire_size=TireSize.ALL_TERRAIN,
        armor_plating=False
    ),

    "prerunner": MonsterConfig(
        chassis_type=ChassisType.PRERUNNER,
        lift_height=0.25,
        tire_size=TireSize.MUD_TERRAIN,
        chassis_visible=True,
        hood_scoops=True,
        exhaust_stacks=True
    ),

    "monster": MonsterConfig(
        chassis_type=ChassisType.MONSTER,
        lift_height=0.5,
        tire_size=TireSize.MONSTER,
        tire_size_multiplier=1.0,
        chassis_visible=True,
        armor_plating=True,
        armor_style=ArmorStyle.INDUSTRIAL,
        spikes=True,
        spike_count=15,
        ram_bars=True,
        rust_level=0.3
    ),

    "apocalypse": MonsterConfig(
        chassis_type=ChassisType.APOCALYPSE,
        lift_height=0.8,
        tire_size=TireSize.MONSTER,
        tire_size_multiplier=1.3,
        chassis_visible=True,
        armor_plating=True,
        armor_style=ArmorStyle.SPIKED,
        armor_coverage=0.8,
        spikes=True,
        spike_count=40,
        spike_length=0.3,
        ram_bars=True,
        ram_bar_style="spike",
        spinning_blades=True,
        improvised_repairs=True,
        duct_tape_patches=10,
        cardboard_windows=True,
        scrap_armor=True,
        door_mismatch=True,
        exhaust_stacks=True,
        skull_decorations=True,
        chains=True,
        barbed_wire=True,
        rust_level=0.7,
        battle_damage=0.5
    ),

    "war_rig": MonsterConfig(
        chassis_type=ChassisType.MONSTER,
        lift_height=0.6,
        tire_size=TireSize.MONSTER,
        chassis_visible=True,
        armor_plating=True,
        armor_style=ArmorStyle.MILITARY,
        armor_coverage=0.9,
        ram_bars=True,
        ram_bar_style="blade",
        flamethrower=True,
        harpoon=True,
        guns_mounted=True,
        spikes=True,
        spike_count=25,
        fuel_tanks=True,
        storage_cages=True,
        rust_level=0.4,
        battle_damage=0.4
    ),

    "scavenger": MonsterConfig(
        chassis_type=ChassisType.LIFTED,
        lift_height=0.3,
        tire_size=TireSize.BOGGER,
        armor_plating=True,
        armor_style=ArmorStyle.SCRAP,
        armor_coverage=0.6,
        improvised_repairs=True,
        duct_tape_patches=8,
        wire_repairs=5,
        scrap_armor=True,
        door_mismatch=True,
        cardboard_windows=True,
        lights_extra=True,
        fuel_tanks=True,
        rust_level=0.6,
        battle_damage=0.4
    ),
}


class MonsterFactory:
    """
    Factory for creating mutant wasteland vehicles.

    Transforms any car into a post-apocalyptic beast with:
    - Lifted/monster chassis
    - Oversized tires
    - Armor and weapons
    - Wasteland weathering
    """

    def __init__(self):
        self.materials: Dict[str, bpy.types.Material] = {}

    def create_monster_car(
        self,
        base_style: str = "sedan",
        config: Optional[MonsterConfig] = None,
        name: str = "MonsterCar",
        position: Vector = None
    ) -> bpy.types.Object:
        """
        Create a monster version of a car.

        Args:
            base_style: Base car style (sedan, sports, suv, etc.)
            config: Monster configuration
            name: Object name
            position: Initial position

        Returns:
            The created monster vehicle
        """
        config = config or MONSTER_PRESETS["monster"]

        # Create base car first
        from .procedural_car import ProceduralCarFactory
        factory = ProceduralCarFactory()
        base_car = factory.create_car(
            name=name,
            style=base_style,
            color="rust",
            position=tuple(position) if position else (0, 0, 0)
        )

        # Apply monster modifications
        self.apply_monster_chassis(base_car, config)
        self.apply_monster_tires(base_car, config)
        self.apply_armor(base_car, config)
        self.apply_weapons(base_car, config)
        self.apply_weathering(base_car, config)
        self.apply_accessories(base_car, config)

        # Setup physics for monster truck
        self.setup_monster_physics(base_car, config)

        return base_car

    def apply_monster_chassis(
        self,
        vehicle: bpy.types.Object,
        config: MonsterConfig
    ) -> bpy.types.Object:
        """Apply chassis modifications (lift, tube frame)."""
        lift = config.lift_height

        # Create tube chassis if visible
        if config.chassis_visible:
            chassis = self._create_tube_chassis(vehicle, config)
            vehicle["chassis"] = chassis

        # Adjust vehicle height
        vehicle.location.z += lift

        # Store chassis config
        vehicle["chassis_type"] = config.chassis_type.value
        vehicle["lift_height"] = lift

        return vehicle

    def _create_tube_chassis(
        self,
        vehicle: bpy.types.Object,
        config: MonsterConfig
    ) -> bpy.types.Object:
        """Create a visible tube chassis."""
        chassis_name = f"{vehicle.name}_chassis"

        # Get vehicle dimensions
        bbox = vehicle.bound_box
        length = max(v[0] for v in bbox) - min(v[0] for v in bbox)
        width = max(v[1] for v in bbox) - min(v[1] for v in bbox)
        height = max(v[2] for v in bbox) - min(v[2] for v in bbox)

        # Create tube chassis mesh
        mesh = bpy.data.meshes.new(f"{chassis_name}_mesh")
        chassis = bpy.data.objects.new(chassis_name, mesh)

        # Create main rails
        rail_positions = [
            (length/2 - 0.3, width/2 - 0.1, 0.2),
            (-length/2 + 0.3, width/2 - 0.1, 0.2),
            (length/2 - 0.3, -width/2 + 0.1, 0.2),
            (-length/2 + 0.3, -width/2 + 0.1, 0.2),
        ]

        import bmesh
        bm = bmesh.new()

        # Create tube vertices (simplified as lines)
        for x, y, z in rail_positions:
            # Rail along length
            for i in range(10):
                t = i / 9
                px = -length/2 + t * length
                bm.verts.new((px, y, z + config.lift_height))

        # Add cross bars
        cross_positions = [-length/3, 0, length/3]
        for cx in cross_positions:
            # Front-back cross
            bm.verts.new((cx, -width/2 + 0.1, 0.4 + config.lift_height))
            bm.verts.new((cx, width/2 - 0.1, 0.4 + config.lift_height))

        bm.verts.ensure_lookup_table()
        bm.to_mesh(mesh)
        bm.free()

        chassis.location = vehicle.location
        chassis.parent = vehicle
        bpy.context.collection.objects.link(chassis)

        # Rust material
        mat = self._get_rust_material()
        chassis.data.materials.append(mat)

        return chassis

    def apply_monster_tires(
        self,
        vehicle: bpy.types.Object,
        config: MonsterConfig
    ) -> List[bpy.types.Object]:
        """Apply oversized monster tires."""
        tires = []

        # Determine tire radius
        tire_sizes = {
            TireSize.STOCK: 0.32,
            TireSize.LOW_PROFILE: 0.28,
            TireSize.ALL_TERRAIN: 0.38,
            TireSize.MUD_TERRAIN: 0.42,
            TireSize.BOGGER: 0.50,
            TireSize.MONSTER: 0.85,
        }

        radius = tire_sizes.get(config.tire_size, 0.35) * config.tire_size_multiplier

        # Get wheel positions from vehicle
        wheel_positions = [
            ("FL", (1.2, 0.7, radius)),
            ("FR", (1.2, -0.7, radius)),
            ("RL", (-1.2, 0.7, radius)),
            ("RR", (-1.2, -0.7, radius)),
        ]

        # Adjust for lift
        for name, pos in wheel_positions:
            adjusted_pos = (pos[0], pos[1], pos[2] + config.lift_height)

            tire = self._create_monster_tire(
                vehicle, name, adjusted_pos, radius, config
            )
            tires.append(tire)

        vehicle["tire_radius"] = radius
        return tires

    def _create_monster_tire(
        self,
        vehicle: bpy.types.Object,
        name: str,
        position: Tuple[float, float, float],
        radius: float,
        config: MonsterConfig
    ) -> bpy.types.Object:
        """Create a single monster tire."""
        tire_name = f"{vehicle.name}_tire_{name}"

        # Create tire mesh (torus-like)
        mesh = bpy.data.meshes.new(f"{tire_name}_mesh")
        tire = bpy.data.objects.new(tire_name, mesh)

        # Create tire shape using bmesh
        import bmesh
        bm = bmesh.new()

        # Create torus for tire
        segments = 32
        ring_segments = 12
        tube_radius = radius * 0.35  # Width of tire

        for i in range(segments):
            angle = 2 * pi * i / segments
            for j in range(ring_segments):
                ring_angle = 2 * pi * j / ring_segments

                x = position[0]
                y = position[1] + (radius + tube_radius * cos(ring_angle)) * cos(angle)
                z = position[2] + (radius + tube_radius * cos(ring_angle)) * sin(angle) + tube_radius * sin(ring_angle)

                bm.verts.new((x, y, z))

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

        tire.parent = vehicle
        bpy.context.collection.objects.link(tire)

        # Tire material (black rubber)
        mat = self._get_tire_material()
        tire.data.materials.append(mat)

        return tire

    def apply_armor(
        self,
        vehicle: bpy.types.Object,
        config: MonsterConfig
    ) -> List[bpy.types.Object]:
        """Apply armor plating to vehicle."""
        if not config.armor_plating:
            return []

        armor_parts = []

        if config.armor_style == ArmorStyle.SCRAP:
            armor_parts = self._add_scrap_armor(vehicle, config)
        elif config.armor_style == ArmorStyle.INDUSTRIAL:
            armor_parts = self._add_industrial_armor(vehicle, config)
        elif config.armor_style == ArmorStyle.MILITARY:
            armor_parts = self._add_military_armor(vehicle, config)
        elif config.armor_style == ArmorStyle.SPIKED:
            armor_parts = self._add_spiked_armor(vehicle, config)

        # Add spikes if enabled
        if config.spikes:
            self._add_spikes(vehicle, config)

        return armor_parts

    def _add_scrap_armor(
        self,
        vehicle: bpy.types.Object,
        config: MonsterConfig
    ) -> List[bpy.types.Object]:
        """Add random scrap metal armor plates."""
        parts = []
        coverage = config.armor_coverage

        # Random plate positions
        num_plates = int(20 * coverage)

        for i in range(num_plates):
            plate = self._create_scrap_plate(vehicle, i)
            parts.append(plate)

        return parts

    def _create_scrap_plate(
        self,
        vehicle: bpy.types.Object,
        index: int
    ) -> bpy.types.Object:
        """Create a single scrap armor plate."""
        plate_name = f"{vehicle.name}_scrap_{index}"

        # Random position on vehicle
        x = random.uniform(-1.5, 1.5)
        y = random.uniform(-0.9, 0.9) if random.random() > 0.5 else random.choice([-0.9, 0.9])
        z = random.uniform(0.3, 1.2)

        # Create plate mesh
        bpy.ops.mesh.primitive_cube_add(size=1)
        plate = bpy.context.active_object
        plate.name = plate_name

        # Random scale
        plate.scale = (
            random.uniform(0.1, 0.4),
            random.uniform(0.2, 0.6),
            random.uniform(0.01, 0.03)
        )

        # Random rotation
        plate.rotation_euler = (
            random.uniform(-0.2, 0.2),
            random.uniform(-0.3, 0.3),
            random.uniform(0, 2 * pi)
        )

        plate.location = (x, y, z + vehicle.location.z)
        plate.parent = vehicle

        # Random metal material
        mat = self._get_scrap_metal_material()
        plate.data.materials.append(mat)

        return plate

    def _add_industrial_armor(
        self,
        vehicle: bpy.types.Object,
        config: MonsterConfig
    ) -> List[bpy.types.Object]:
        """Add welded industrial steel armor."""
        parts = []

        # Front bumper/grill guard
        front = self._create_grill_guard(vehicle, config)
        parts.append(front)

        # Side panels
        for side in ['left', 'right']:
            panel = self._create_side_panel(vehicle, side, config)
            parts.append(panel)

        return parts

    def _create_grill_guard(
        self,
        vehicle: bpy.types.Object,
        config: MonsterConfig
    ) -> bpy.types.Object:
        """Create front grill guard."""
        guard_name = f"{vehicle.name}_grill_guard"

        mesh = bpy.data.meshes.new(f"{guard_name}_mesh")
        guard = bpy.data.objects.new(guard_name, mesh)

        # Create vertical and horizontal bars
        import bmesh
        bm = bmesh.new()

        # Vertical bars
        for y in [-0.6, -0.3, 0, 0.3, 0.6]:
            v1 = bm.verts.new((1.8, y, 0.3))
            v2 = bm.verts.new((1.8, y, 1.0))

        # Horizontal bars
        for z in [0.3, 0.6, 0.9]:
            v1 = bm.verts.new((1.8, -0.7, z))
            v2 = bm.verts.new((1.8, 0.7, z))

        bm.to_mesh(mesh)
        bm.free()

        guard.parent = vehicle
        bpy.context.collection.objects.link(guard)

        mat = self._get_metal_material()
        guard.data.materials.append(mat)

        return guard

    def _create_side_panel(
        self,
        vehicle: bpy.types.Object,
        side: str,
        config: MonsterConfig
    ) -> bpy.types.Object:
        """Create side armor panel."""
        y_offset = 0.95 if side == 'left' else -0.95

        panel_name = f"{vehicle.name}_armor_{side}"

        bpy.ops.mesh.primitive_cube_add(size=1)
        panel = bpy.context.active_object
        panel.name = panel_name

        panel.scale = (2.5, 0.05, 0.6)
        panel.location = (0, y_offset, 0.7 + config.lift_height)
        panel.parent = vehicle

        mat = self._get_metal_material()
        panel.data.materials.append(mat)

        return panel

    def _add_military_armor(
        self,
        vehicle: bpy.types.Object,
        config: MonsterConfig
    ) -> List[bpy.types.Object]:
        """Add military-style armored plates."""
        parts = []

        # Angular armor plates
        for side in ['left', 'right', 'front', 'rear']:
            plate = self._create_armor_plate(vehicle, side, config)
            parts.append(plate)

        return parts

    def _create_armor_plate(
        self,
        vehicle: bpy.types.Object,
        position: str,
        config: MonsterConfig
    ) -> bpy.types.Object:
        """Create an angular armor plate."""
        plate_name = f"{vehicle.name}_armor_{position}"

        bpy.ops.mesh.primitive_cube_add(size=1)
        plate = bpy.context.active_object
        plate.name = plate_name

        # Position-specific placement
        positions = {
            'front': ((1.9, 0, 0.7), (0.2, 1.2, 0.8)),
            'rear': ((-1.9, 0, 0.7), (0.2, 1.2, 0.8)),
            'left': ((0, 1.0, 0.7), (2.2, 0.1, 0.7)),
            'right': ((0, -1.0, 0.7), (2.2, 0.1, 0.7)),
        }

        loc, scale = positions.get(position, ((0, 0, 0.5), (1, 1, 0.1)))
        plate.location = (loc[0], loc[1], loc[2] + config.lift_height)
        plate.scale = scale

        # Angled
        if position in ['front', 'rear']:
            plate.rotation_euler = (0.2, 0, 0)

        plate.parent = vehicle

        mat = self._get_military_armor_material()
        plate.data.materials.append(mat)

        return plate

    def _add_spiked_armor(
        self,
        vehicle: bpy.types.Object,
        config: MonsterConfig
    ) -> List[bpy.types.Object]:
        """Add armor covered in spikes."""
        parts = self._add_industrial_armor(vehicle, config)
        self._add_spikes(vehicle, config)
        return parts

    def _add_spikes(
        self,
        vehicle: bpy.types.Object,
        config: MonsterConfig
    ) -> List[bpy.types.Object]:
        """Add spikes all over the vehicle."""
        spikes = []

        for i in range(config.spike_count):
            spike = self._create_spike(vehicle, i, config)
            if spike:
                spikes.append(spike)

        return spikes

    def _create_spike(
        self,
        vehicle: bpy.types.Object,
        index: int,
        config: MonsterConfig
    ) -> Optional[bpy.types.Object]:
        """Create a single spike."""
        spike_name = f"{vehicle.name}_spike_{index}"

        # Random position on vehicle surface
        face = random.choice(['top', 'front', 'left', 'right'])
        length = config.spike_length * random.uniform(0.7, 1.3)

        if face == 'top':
            pos = (random.uniform(-1.5, 1.5), random.uniform(-0.7, 0.7), 1.3)
            rot = (0, 0, random.uniform(0, 2*pi))
        elif face == 'front':
            pos = (2.0, random.uniform(-0.7, 0.7), random.uniform(0.3, 1.0))
            rot = (pi/2, 0, 0)
        elif face == 'left':
            pos = (random.uniform(-1.5, 1.5), 0.95, random.uniform(0.3, 1.0))
            rot = (0, 0, pi/2)
        else:  # right
            pos = (random.uniform(-1.5, 1.5), -0.95, random.uniform(0.3, 1.0))
            rot = (0, 0, -pi/2)

        # Create cone for spike
        bpy.ops.mesh.primitive_cone_add(
            radius1=0.02,
            radius2=0,
            depth=length,
            location=pos
        )
        spike = bpy.context.active_object
        spike.name = spike_name
        spike.rotation_euler = rot
        spike.parent = vehicle

        # Sharp metal material
        mat = self._get_spike_material()
        spike.data.materials.append(mat)

        return spike

    def apply_weapons(
        self,
        vehicle: bpy.types.Object,
        config: MonsterConfig
    ) -> List[bpy.types.Object]:
        """Apply visual weapons to vehicle."""
        weapons = []

        if config.ram_bars:
            ram = self._create_ram_bars(vehicle, config)
            weapons.append(ram)

        if config.spinning_blades:
            blades = self._create_spinning_blades(vehicle, config)
            weapons.extend(blades)

        if config.flamethrower:
            ft = self._create_flamethrower(vehicle, config)
            weapons.append(ft)

        return weapons

    def _create_ram_bars(
        self,
        vehicle: bpy.types.Object,
        config: MonsterConfig
    ) -> bpy.types.Object:
        """Create front ram bars."""
        ram_name = f"{vehicle.name}_ram"

        bpy.ops.mesh.primitive_cube_add(size=1)
        ram = bpy.context.active_object
        ram.name = ram_name

        if config.ram_bar_style == "spike":
            ram.scale = (0.3, 1.5, 0.2)
            ram.location = (2.1, 0, 0.5 + config.lift_height)
        elif config.ram_bar_style == "blade":
            ram.scale = (0.1, 1.8, 0.4)
            ram.location = (2.1, 0, 0.4 + config.lift_height)
            ram.rotation_euler = (0.3, 0, 0)
        else:  # push
            ram.scale = (0.2, 1.6, 0.3)
            ram.location = (2.1, 0, 0.5 + config.lift_height)

        ram.parent = vehicle

        mat = self._get_metal_material()
        ram.data.materials.append(mat)

        return ram

    def _create_spinning_blades(
        self,
        vehicle: bpy.types.Object,
        config: MonsterConfig
    ) -> List[bpy.types.Object]:
        """Create spinning blade assemblies."""
        blades = []

        for side in ['left', 'right']:
            blade_name = f"{vehicle.name}_blade_{side}"

            # Create blade hub
            bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.1)
            hub = bpy.context.active_object
            hub.name = blade_name

            y = 1.1 if side == 'left' else -1.1
            hub.location = (0, y, 0.6 + config.lift_height)
            hub.rotation_euler = (pi/2, 0, 0)
            hub.parent = vehicle

            # Add blade spokes
            for i in range(4):
                angle = i * pi / 2

                bpy.ops.mesh.primitive_cube_add(size=1)
                blade = bpy.context.active_object

                blade.scale = (0.02, 0.4, 0.05)
                blade.location = (0.2 * sin(angle), y, 0.6 + config.lift_height + 0.2 * cos(angle))
                blade.rotation_euler = (0, angle, 0)
                blade.parent = hub

                mat = self._get_spike_material()
                blade.data.materials.append(mat)

            mat = self._get_metal_material()
            hub.data.materials.append(mat)

            blades.append(hub)

        return blades

    def _create_flamethrower(
        self,
        vehicle: bpy.types.Object,
        config: MonsterConfig
    ) -> bpy.types.Object:
        """Create flamethrower assembly (visual only)."""
        ft_name = f"{vehicle.name}_flamethrower"

        # Create nozzle
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.3)
        nozzle = bpy.context.active_object
        nozzle.name = ft_name

        nozzle.location = (-1.8, 0, 0.8 + config.lift_height)
        nozzle.rotation_euler = (0, pi/2, 0)
        nozzle.parent = vehicle

        mat = self._get_metal_material()
        nozzle.data.materials.append(mat)

        return nozzle

    def apply_weathering(
        self,
        vehicle: bpy.types.Object,
        config: MonsterConfig
    ) -> None:
        """Apply wasteland weathering."""
        from .weathering import apply_weathering, WeatheringConfig, DirtPattern, RustSeverity

        weathering = WeatheringConfig(
            dirt_level=0.7,
            dirt_pattern=DirtPattern.OFFROAD,
            sun_fade=0.3,
            clear_coat_wear=0.8,
            scratches=int(30 * config.battle_damage),
            paint_chips=int(50 * config.battle_damage),
            rust_spots=int(20 * config.rust_level),
            rust_severity=RustSeverity.HEAVY if config.rust_level > 0.5 else RustSeverity.SPOT,
            mud_splatter=True,
            bumper_scuffs=True,
            wheel_well_grime=True
        )

        apply_weathering(vehicle, custom_config=weathering)

    def apply_accessories(
        self,
        vehicle: bpy.types.Object,
        config: MonsterConfig
    ) -> List[bpy.types.Object]:
        """Apply additional accessories."""
        accessories = []

        if config.exhaust_stacks:
            stacks = self._add_exhaust_stacks(vehicle, config)
            accessories.extend(stacks)

        if config.fuel_tanks:
            tanks = self._add_fuel_tanks(vehicle, config)
            accessories.extend(tanks)

        if config.lights_extra:
            lights = self._add_extra_lights(vehicle, config)
            accessories.extend(lights)

        if config.improvised_repairs:
            self._add_improvised_repairs(vehicle, config)

        return accessories

    def _add_exhaust_stacks(
        self,
        vehicle: bpy.types.Object,
        config: MonsterConfig
    ) -> List[bpy.types.Object]:
        """Add vertical exhaust stacks."""
        stacks = []

        for side in ['left', 'right']:
            stack_name = f"{vehicle.name}_exhaust_{side}"

            bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=1.2)
            stack = bpy.context.active_object
            stack.name = stack_name

            y = 0.7 if side == 'left' else -0.7
            stack.location = (-1.3, y, 1.2 + config.lift_height)
            stack.parent = vehicle

            mat = self._get_metal_material()
            stack.data.materials.append(mat)

            stacks.append(stack)

        return stacks

    def _add_fuel_tanks(
        self,
        vehicle: bpy.types.Object,
        config: MonsterConfig
    ) -> List[bpy.types.Object]:
        """Add external fuel tanks."""
        tanks = []

        for side in ['left', 'right']:
            tank_name = f"{vehicle.name}_fuel_{side}"

            bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=0.8)
            tank = bpy.context.active_object
            tank.name = tank_name
            tank.rotation_euler = (pi/2, 0, 0)

            y = 0.9 if side == 'left' else -0.9
            tank.location = (-0.8, y, 1.0 + config.lift_height)
            tank.parent = vehicle

            mat = self._get_rust_material()
            tank.data.materials.append(mat)

            tanks.append(tank)

        return tanks

    def _add_extra_lights(
        self,
        vehicle: bpy.types.Object,
        config: MonsterConfig
    ) -> List[bpy.types.Object]:
        """Add extra offroad lights."""
        lights = []

        for i in range(4):
            light_name = f"{vehicle.name}_light_{i}"

            bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=0.05)
            light = bpy.context.active_object
            light.name = light_name
            light.rotation_euler = (0, pi/2, 0)

            y = -0.5 + i * 0.35
            light.location = (2.0, y, 1.1 + config.lift_height)
            light.parent = vehicle

            # Emissive material
            mat = self._get_light_material()
            light.data.materials.append(mat)

            lights.append(light)

        return lights

    def _add_improvised_repairs(
        self,
        vehicle: bpy.types.Object,
        config: MonsterConfig
    ) -> None:
        """Add visual improvised repairs (duct tape, wire)."""
        # This would add decals or small objects representing repairs
        # Simplified for now
        pass

    def setup_monster_physics(
        self,
        vehicle: bpy.types.Object,
        config: MonsterConfig
    ) -> None:
        """Setup physics for monster truck."""
        from .physics_core import PhysicsEngine, VehiclePhysics, DrivetrainType

        physics = VehiclePhysics(
            mass=4500.0 if config.chassis_type == ChassisType.MONSTER else 2500.0,
            max_power=750.0 if config.chassis_type == ChassisType.MONSTER else 300.0,
            max_torque=1200.0 if config.chassis_type == ChassisType.MONSTER else 500.0,
            drivetrain=DrivetrainType.FOUR_WD,
            center_of_gravity_height=0.8 + config.lift_height,
            tire_radius_front=0.85 if config.tire_size == TireSize.MONSTER else 0.42,
            tire_radius_rear=0.85 if config.tire_size == TireSize.MONSTER else 0.42,
        )

        engine = PhysicsEngine()
        engine.setup_rigid_body(vehicle, physics)

    # === MATERIALS ===

    def _get_rust_material(self) -> bpy.types.Material:
        """Get or create rust material."""
        name = "monster_rust"

        if name in bpy.data.materials:
            return bpy.data.materials[name]

        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.45, 0.25, 0.15, 1.0)
            bsdf.inputs["Metallic"].default_value = 0.3
            bsdf.inputs["Roughness"].default_value = 0.9

        return mat

    def _get_metal_material(self) -> bpy.types.Material:
        """Get or create metal material."""
        name = "monster_metal"

        if name in bpy.data.materials:
            return bpy.data.materials[name]

        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.3, 0.3, 0.32, 1.0)
            bsdf.inputs["Metallic"].default_value = 0.9
            bsdf.inputs["Roughness"].default_value = 0.4

        return mat

    def _get_scrap_metal_material(self) -> bpy.types.Material:
        """Get or create scrap metal material."""
        name = "monster_scrap"

        if name in bpy.data.materials:
            return bpy.data.materials[name]

        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # Random tint per object would be better
            bsdf.inputs["Base Color"].default_value = (0.35, 0.32, 0.3, 1.0)
            bsdf.inputs["Metallic"].default_value = 0.7
            bsdf.inputs["Roughness"].default_value = 0.7

        return mat

    def _get_military_armor_material(self) -> bpy.types.Material:
        """Get or create military armor material."""
        name = "monster_armor"

        if name in bpy.data.materials:
            return bpy.data.materials[name]

        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.2, 0.22, 0.18, 1.0)
            bsdf.inputs["Metallic"].default_value = 0.5
            bsdf.inputs["Roughness"].default_value = 0.6

        return mat

    def _get_spike_material(self) -> bpy.types.Material:
        """Get or create spike material."""
        name = "monster_spike"

        if name in bpy.data.materials:
            return bpy.data.materials[name]

        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.6, 0.6, 0.62, 1.0)
            bsdf.inputs["Metallic"].default_value = 0.95
            bsdf.inputs["Roughness"].default_value = 0.3

        return mat

    def _get_tire_material(self) -> bpy.types.Material:
        """Get or create tire material."""
        name = "monster_tire"

        if name in bpy.data.materials:
            return bpy.data.materials[name]

        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.08, 0.08, 0.08, 1.0)
            bsdf.inputs["Metallic"].default_value = 0.0
            bsdf.inputs["Roughness"].default_value = 0.9

        return mat

    def _get_light_material(self) -> bpy.types.Material:
        """Get or create light material."""
        name = "monster_light"

        if name in bpy.data.materials:
            return bpy.data.materials[name]

        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (1.0, 0.95, 0.8, 1.0)
            bsdf.inputs["Emission"].default_value = (1.0, 0.95, 0.8, 1.0)
            bsdf.inputs["Emission Strength"].default_value = 10.0

        return mat


# === CONVENIENCE FUNCTIONS ===

def create_monster_car(
    base_style: str = "sedan",
    preset: str = "monster",
    custom_config: Optional[MonsterConfig] = None,
    name: str = "MonsterCar",
    position: Vector = None
) -> bpy.types.Object:
    """
    Convenience function to create a monster car.

    Args:
        base_style: Base car style
        preset: Monster preset name
        custom_config: Override config
        name: Object name
        position: Initial position

    Returns:
        The created monster vehicle
    """
    config = custom_config or MONSTER_PRESETS.get(preset, MONSTER_PRESETS["monster"])
    factory = MonsterFactory()
    return factory.create_monster_car(base_style, config, name, position)


def get_monster_preset(preset_name: str) -> MonsterConfig:
    """Get a monster preset by name."""
    return MONSTER_PRESETS.get(preset_name, MONSTER_PRESETS["monster"])


def list_monster_presets() -> List[str]:
    """List available monster presets."""
    return list(MONSTER_PRESETS.keys())
