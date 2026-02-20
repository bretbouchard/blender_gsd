"""
Damage System - Crumple Zones, Deformation, and Detachable Parts

Provides physics-based damage and deformation for vehicles.
From minor dents to total destruction.

Usage:
    from lib.animation.vehicle.damage import (
        DamageConfig, DamageZone, DamageSystem, apply_impact_damage
    )

    # Setup damage zones
    config = DamageConfig(detachable_parts=["bumper_front", "bumper_rear"])
    system = DamageSystem()
    system.setup_crumple_zones(vehicle, config)

    # Apply impact
    system.apply_impact(
        vehicle=vehicle,
        impact_point=Vector((1.5, 0.3, 0.5)),
        impact_force=Vector((-50000, 0, 0)),
        impact_radius=0.8
    )
"""

import bpy
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from math import pi, sin, cos, sqrt, exp
from mathutils import Vector, Matrix, Quaternion
from enum import Enum
import random


class DamageType(Enum):
    IMPACT = "impact"           # Collision with object
    SCRAPE = "scrape"           # Dragging along surface
    CRUSH = "crush"             # Compression damage
    PENETRATION = "penetration" # Deep puncture
    ROLLOVER = "rollover"       # Roof damage
    EXPLOSION = "explosion"     # Blast damage


class DamageSeverity(Enum):
    NONE = "none"               # 0%
    MINOR = "minor"             # 1-20%
    MODERATE = "moderate"       # 21-40%
    SEVERE = "severe"           # 41-60%
    CRITICAL = "critical"       # 61-80%
    DESTROYED = "destroyed"     # 81-100%


@dataclass
class DamageZone:
    """Configuration for a crumple zone on the vehicle."""

    name: str
    vertices: List[int] = field(default_factory=list)
    center: Vector = field(default_factory=lambda: Vector((0, 0, 0)))
    radius: float = 0.5

    # Physics properties
    stiffness: float = 1.0              # Resistance to deformation
    max_deformation: float = 0.3        # Max displacement (fraction)
    elasticity: float = 0.1             # How much springs back

    # Part attachment
    detachable: bool = False
    detach_threshold: float = 50000.0   # Force to detach

    # Visual
    deform_style: str = "crumple"       # crumple, dent, crush


@dataclass
class DamageConfig:
    """Configuration for vehicle damage system."""

    # === CRUMPLE ZONES ===
    zones: List[DamageZone] = field(default_factory=list)

    # === GLASS ===
    glass_shatter: bool = True
    glass_shatter_force: float = 30000.0

    # === DETACHABLE PARTS ===
    detachable_parts: List[str] = field(default_factory=lambda: [
        "bumper_front", "bumper_rear",
        "mirror_left", "mirror_right",
        "door_FL", "door_FR", "door_RL", "door_RR",
        "hood", "trunk", "windshield", "rear_window"
    ])

    # === DEFORMATION ===
    global_deformation: bool = True
    deformation_decay: float = 0.5       # How quickly deformation falls off

    # === VISUAL ===
    damage_material_blend: bool = True   # Blend to damaged material
    scratch_on_impact: bool = True

    # === SIMULATION ===
    simulation_steps: int = 10           # Substeps for deformation


@dataclass
class DamageState:
    """Current damage state of a vehicle."""

    overall_damage: float = 0.0          # 0-1
    zones_damaged: Dict[str, float] = field(default_factory=dict)
    detached_parts: List[str] = field(default_factory=list)
    shattered_glass: List[str] = field(default_factory=list)

    # Deformation data
    vertex_displacements: Dict[int, Vector] = field(default_factory=dict)

    def get_severity(self) -> DamageSeverity:
        """Get overall damage severity level."""
        if self.overall_damage < 0.01:
            return DamageSeverity.NONE
        elif self.overall_damage < 0.2:
            return DamageSeverity.MINOR
        elif self.overall_damage < 0.4:
            return DamageSeverity.MODERATE
        elif self.overall_damage < 0.6:
            return DamageSeverity.SEVERE
        elif self.overall_damage < 0.8:
            return DamageSeverity.CRITICAL
        else:
            return DamageSeverity.DESTROYED


# === DAMAGE PRESETS ===

DAMAGE_PRESETS = {
    "none": DamageConfig(
        detachable_parts=[],
        glass_shatter=False
    ),

    "minor": DamageConfig(
        detachable_parts=["mirror_left", "mirror_right"],
        glass_shatter=True,
        global_deformation=False
    ),

    "standard": DamageConfig(
        detachable_parts=[
            "bumper_front", "bumper_rear",
            "mirror_left", "mirror_right",
            "hood"
        ],
        glass_shatter=True
    ),

    "heavy": DamageConfig(
        detachable_parts=[
            "bumper_front", "bumper_rear",
            "mirror_left", "mirror_right",
            "door_FL", "door_FR", "door_RL", "door_RR",
            "hood", "trunk"
        ],
        glass_shatter=True,
        global_deformation=True
    ),

    "destruction": DamageConfig(
        detachable_parts=[
            "bumper_front", "bumper_rear",
            "mirror_left", "mirror_right",
            "door_FL", "door_FR", "door_RL", "door_RR",
            "hood", "trunk",
            "windshield", "rear_window"
        ],
        glass_shatter=True,
        global_deformation=True,
        deformation_decay=0.3
    )
}


class DamageSystem:
    """
    Physics-based damage and deformation system.

    Handles:
    - Crumple zone deformation
    - Part detachment
    - Glass shattering
    - Visual damage materials
    """

    def __init__(self):
        self.damage_states: Dict[str, DamageState] = {}
        self.damage_material: Optional[bpy.types.Material] = None

    def setup_crumple_zones(
        self,
        vehicle: bpy.types.Object,
        config: DamageConfig
    ) -> List[DamageZone]:
        """
        Setup crumple zones for a vehicle.

        Creates default zones if none specified.

        Args:
            vehicle: The vehicle object
            config: Damage configuration

        Returns:
            List of configured damage zones
        """
        if vehicle.type != 'MESH':
            return []

        # Create default zones if not specified
        if not config.zones:
            config.zones = self._create_default_zones(vehicle)

        # Initialize damage state
        state = DamageState()
        for zone in config.zones:
            state.zones_damaged[zone.name] = 0.0

        self.damage_states[vehicle.name] = state
        vehicle["damage_config"] = config
        vehicle["damage_state"] = state

        # Create damage material
        self.damage_material = self._get_or_create_damage_material()

        return config.zones

    def _create_default_zones(self, vehicle: bpy.types.Object) -> List[DamageZone]:
        """Create default crumple zones based on vehicle bounding box."""
        bbox = vehicle.bound_box

        min_x = min(v[0] for v in bbox)
        max_x = max(v[0] for v in bbox)
        min_y = min(v[1] for v in bbox)
        max_y = max(v[1] for v in bbox)
        min_z = min(v[2] for v in bbox)
        max_z = max(v[2] for v in bbox)

        length = max_x - min_x
        width = max_y - min_y
        height = max_z - min_z

        zones = [
            # Front crumple zone
            DamageZone(
                name="front",
                center=Vector((max_x - length * 0.15, 0, min_z + height * 0.5)),
                radius=length * 0.25,
                stiffness=0.7,
                max_deformation=0.4,
                detachable=True,
                detach_threshold=40000.0
            ),

            # Rear crumple zone
            DamageZone(
                name="rear",
                center=Vector((min_x + length * 0.15, 0, min_z + height * 0.5)),
                radius=length * 0.25,
                stiffness=0.7,
                max_deformation=0.4,
                detachable=True,
                detach_threshold=40000.0
            ),

            # Left side
            DamageZone(
                name="left",
                center=Vector((0, max_y - width * 0.1, min_z + height * 0.5)),
                radius=width * 0.3,
                stiffness=0.9,
                max_deformation=0.2
            ),

            # Right side
            DamageZone(
                name="right",
                center=Vector((0, min_y + width * 0.1, min_z + height * 0.5)),
                radius=width * 0.3,
                stiffness=0.9,
                max_deformation=0.2
            ),

            # Roof
            DamageZone(
                name="roof",
                center=Vector((0, 0, max_z - height * 0.1)),
                radius=width * 0.4,
                stiffness=0.6,
                max_deformation=0.35
            ),

            # Hood
            DamageZone(
                name="hood",
                center=Vector((max_x - length * 0.25, 0, min_z + height * 0.7)),
                radius=length * 0.2,
                stiffness=0.5,
                max_deformation=0.3,
                detachable=True,
                detach_threshold=35000.0
            ),
        ]

        # Assign vertices to zones
        mesh = vehicle.data
        for vert in mesh.vertices:
            for zone in zones:
                if (vert.co - zone.center).length < zone.radius:
                    zone.vertices.append(vert.index)

        return zones

    def apply_impact(
        self,
        vehicle: bpy.types.Object,
        impact_point: Vector,
        impact_force: Vector,
        impact_radius: float = 0.5,
        impact_type: DamageType = DamageType.IMPACT
    ) -> DamageState:
        """
        Apply impact damage to vehicle.

        Args:
            vehicle: The vehicle object
            impact_point: World-space impact location
            impact_force: Force vector (direction + magnitude)
            impact_radius: Radius of impact area
            impact_type: Type of damage

        Returns:
            Updated damage state
        """
        config = vehicle.get("damage_config")
        state = self.damage_states.get(vehicle.name)

        if not config or not state or vehicle.type != 'MESH':
            return state

        # Convert impact point to local space
        inv_matrix = vehicle.matrix_world.inverted()
        local_point = inv_matrix @ impact_point

        # Get impact magnitude
        force_magnitude = impact_force.length

        # Find affected zones
        for zone in config.zones:
            distance = (local_point - zone.center).length
            if distance < zone.radius + impact_radius:
                # Calculate damage to this zone
                overlap = 1.0 - (distance / (zone.radius + impact_radius))
                damage_force = force_magnitude * overlap

                # Apply deformation
                deformation = self._calculate_deformation(
                    zone, damage_force, local_point, impact_force.normalized()
                )

                # Update zone damage
                zone_damage = min(1.0, zone.stiffness * damage_force / 50000.0)
                state.zones_damaged[zone.name] = min(1.0,
                    state.zones_damaged[zone.name] + zone_damage * overlap
                )

                # Check for detachment
                if zone.detachable and damage_force > zone.detach_threshold:
                    self._detach_part(vehicle, zone.name, impact_force)
                    state.detached_parts.append(zone.name)

                # Apply vertex deformation
                self._apply_vertex_deformation(
                    vehicle, zone, local_point, deformation, impact_radius
                )

        # Check for glass shatter
        if config.glass_shatter:
            self._check_glass_shatter(vehicle, local_point, force_magnitude, state)

        # Update overall damage
        state.overall_damage = sum(state.zones_damaged.values()) / max(1, len(config.zones))

        # Apply visual damage material
        if config.damage_material_blend:
            self._apply_damage_material(vehicle, state)

        return state

    def _calculate_deformation(
        self,
        zone: DamageZone,
        force: float,
        impact_point: Vector,
        direction: Vector
    ) -> Vector:
        """Calculate deformation vector for an impact."""
        # Base deformation from force and stiffness
        base_deform = force / (zone.stiffness * 100000.0)

        # Clamp to max deformation
        base_deform = min(base_deform, zone.max_deformation)

        # Direction-based deformation
        # Impact pushes in the direction of force
        deform_vector = direction * base_deform

        return deform_vector

    def _apply_vertex_deformation(
        self,
        vehicle: bpy.types.Object,
        zone: DamageZone,
        impact_point: Vector,
        deformation: Vector,
        radius: float
    ) -> None:
        """Apply deformation to vertices in a zone."""
        mesh = vehicle.data

        # Need to be in edit mode or use bmesh for deformation
        # For simplicity, store displacements for later application
        for vert_idx in zone.vertices:
            vert = mesh.vertices[vert_idx]
            distance = (vert.co - impact_point).length

            if distance < radius:
                # Falloff from impact center
                falloff = 1.0 - (distance / radius)
                falloff = falloff * falloff  # Quadratic falloff

                # Calculate displacement
                displacement = deformation * falloff

                # Store or apply
                if vert_idx not in self.damage_states[vehicle.name].vertex_displacements:
                    self.damage_states[vehicle.name].vertex_displacements[vert_idx] = Vector((0, 0, 0))

                self.damage_states[vehicle.name].vertex_displacements[vert_idx] += displacement

    def _detach_part(
        self,
        vehicle: bpy.types.Object,
        part_name: str,
        force: Vector
    ) -> Optional[bpy.types.Object]:
        """Detach a part from the vehicle."""
        # Find the part (could be a child object or part of mesh)
        part_obj = bpy.data.objects.get(f"{vehicle.name}_{part_name}")

        if part_obj:
            # Unparent from vehicle
            part_obj.parent = None

            # Add rigid body physics
            if not part_obj.rigid_body:
                bpy.context.view_layer.objects.active = part_obj
                bpy.ops.rigidbody.object_add()
                part_obj.rigid_body.type = 'ACTIVE'
                part_obj.rigid_body.mass = 5.0

            # Apply initial velocity from impact
            # (In practice, this would be done through animation or physics)
            part_obj.location = part_obj.matrix_world.translation

            return part_obj

        return None

    def _check_glass_shatter(
        self,
        vehicle: bpy.types.Object,
        impact_point: Vector,
        force: float,
        state: DamageState
    ) -> None:
        """Check if glass should shatter from impact."""
        # Simplified: shatter glass if force exceeds threshold
        if force > 30000.0:
            # Determine which windows to shatter based on impact location
            windows = []

            if impact_point.x > 0.5:
                windows.append("windshield")
            if impact_point.x < -0.5:
                windows.append("rear_window")
            if impact_point.y > 0.3:
                windows.extend(["window_FL", "window_RL"])
            if impact_point.y < -0.3:
                windows.extend(["window_FR", "window_RR"])

            for window in windows:
                if window not in state.shattered_glass:
                    self._shatter_glass(vehicle, window)
                    state.shattered_glass.append(window)

    def _shatter_glass(self, vehicle: bpy.types.Object, window_name: str) -> None:
        """Shatter a window into pieces."""
        # In a full implementation, this would:
        # 1. Find the window mesh/face
        # 2. Create fracture pieces
        # 3. Add physics to pieces
        # 4. Apply outward velocity

        # For now, store the shattered state
        if "shattered_glass" not in vehicle:
            vehicle["shattered_glass"] = []

        vehicle["shattered_glass"].append(window_name)

    def _apply_damage_material(
        self,
        vehicle: bpy.types.Object,
        state: DamageState
    ) -> None:
        """Apply visual damage material blending."""
        damage_level = state.overall_damage

        # Get or create damage vertex color layer
        if vehicle.type != 'MESH':
            return

        mesh = vehicle.data

        if "DamageMask" not in mesh.color_attributes:
            layer = mesh.color_attributes.new(name="DamageMask", type='BYTE_COLOR', domain='CORNER')
        else:
            layer = mesh.color_attributes["DamageMask"]

        # Apply damage color based on vertex displacements
        for i, loop in enumerate(mesh.loops):
            vert_idx = loop.vertex_index
            local_damage = 0.0

            if vert_idx in state.vertex_displacements:
                local_damage = min(1.0, state.vertex_displacements[vert_idx].length * 5)

            # Damage color (darker, more metallic)
            layer.data[i].color = (local_damage, local_damage * 0.3, local_damage * 0.2, 1.0)

    def _get_or_create_damage_material(self) -> bpy.types.Material:
        """Create or get the damage material."""
        name = "vehicle_damage"

        if name in bpy.data.materials:
            return bpy.data.materials[name]

        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # Dark, scratched metal appearance
            bsdf.inputs["Base Color"].default_value = (0.15, 0.15, 0.18, 1.0)
            bsdf.inputs["Metallic"].default_value = 0.6
            bsdf.inputs["Roughness"].default_value = 0.7

        return mat

    def get_damage_state(self, vehicle: bpy.types.Object) -> Optional[DamageState]:
        """Get current damage state for a vehicle."""
        return self.damage_states.get(vehicle.name)

    def set_damage_level(
        self,
        vehicle: bpy.types.Object,
        level: float
    ) -> None:
        """
        Set overall damage level (0-1).

        Applies visual damage without physics simulation.

        Args:
            vehicle: The vehicle object
            level: Damage level (0=pristine, 1=destroyed)
        """
        state = self.damage_states.get(vehicle.name)
        if not state:
            state = DamageState()
            self.damage_states[vehicle.name] = state

        state.overall_damage = level

        # Distribute to zones
        config = vehicle.get("damage_config")
        if config:
            for zone_name in state.zones_damaged:
                state.zones_damaged[zone_name] = level * random.uniform(0.7, 1.0)

        # Apply visual
        self._apply_damage_material(vehicle, state)

    def repair(
        self,
        vehicle: bpy.types.Object,
        amount: float = 1.0
    ) -> float:
        """
        Repair damage on a vehicle.

        Args:
            vehicle: The vehicle object
            amount: Amount to repair (0-1, 1=full repair)

        Returns:
            New damage level
        """
        state = self.damage_states.get(vehicle.name)
        if not state:
            return 0.0

        state.overall_damage = max(0, state.overall_damage - amount)

        for zone_name in state.zones_damaged:
            state.zones_damaged[zone_name] = max(0,
                state.zones_damaged[zone_name] - amount
            )

        # Clear vertex displacements
        if amount >= 1.0:
            state.vertex_displacements.clear()
            state.detached_parts.clear()
            state.shattered_glass.clear()

        # Update visual
        self._apply_damage_material(vehicle, state)

        return state.overall_damage


def apply_impact_damage(
    vehicle: bpy.types.Object,
    impact_point: Vector,
    impact_force: Vector,
    preset: str = "standard"
) -> DamageState:
    """
    Convenience function to apply impact damage.

    Args:
        vehicle: The vehicle object
        impact_point: World-space impact location
        impact_force: Force vector
        preset: Damage config preset

    Returns:
        Updated damage state
    """
    config = DAMAGE_PRESETS.get(preset, DAMAGE_PRESETS["standard"])
    system = DamageSystem()
    system.setup_crumple_zones(vehicle, config)
    return system.apply_impact(vehicle, impact_point, impact_force)


def get_damage_preset(preset_name: str) -> DamageConfig:
    """Get a damage preset by name."""
    return DAMAGE_PRESETS.get(preset_name, DAMAGE_PRESETS["standard"])


def list_damage_presets() -> List[str]:
    """List available damage presets."""
    return list(DAMAGE_PRESETS.keys())
