"""
Suspension System - Real Spring-Damper Physics

Provides physics-based suspension with proper spring-damper model,
terrain following, and anti-roll bars.

Usage:
    from lib.animation.vehicle.suspension_physics import (
        SuspensionPhysics, SuspensionSystem, setup_suspension
    )

    config = SuspensionPhysics(
        spring_rate=35000.0,
        damping_coefficient=4000.0,
        travel=0.15
    )

    suspension = SuspensionSystem()
    suspension.create_suspension_rig(wheel_pivot, config)
    compression = suspension.simulate_tick(suspension_data, terrain_height)
"""

import bpy
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from math import pi, sqrt, exp, sin, cos
from mathutils import Vector, Matrix
from enum import Enum


class SuspensionType(Enum):
    INDEPENDENT = "independent"
    SOLID_AXLE = "solid_axle"
    MACPHERSON = "macpherson"
    DOUBLE_WISHBONE = "double_wishbone"
    MULTILINK = "multilink"
    LIVE_AXLE = "live_axle"


@dataclass
class SuspensionPhysics:
    """
    Spring-damper suspension parameters.

    The suspension uses the classic spring-damper equation:
    F = -k*x - c*v

    Where:
    - k = spring rate (N/m)
    - c = damping coefficient (Ns/m)
    - x = displacement from rest
    - v = velocity of displacement
    """

    # === SPRING PARAMETERS ===
    spring_rate: float = 35000.0          # N/m (stiffness)
    damping_coefficient: float = 4000.0   # Ns/m (damping)
    travel: float = 0.15                  # m (total travel, ± from rest)

    # === ADVANCED SPRING ===
    progressive_rate: bool = False        # Spring gets stiffer as compressed
    progressive_factor: float = 1.2       # Rate multiplier at full compression
    bump_stop_force: float = 50000.0      # N (hard stop at travel limit)
    bump_stop_compression: float = 0.02   # m (bump stop engagement point)

    # === GEOMETRY ===
    camber: float = -0.5                  # degrees (negative = top in)
    caster: float = 5.0                   # degrees (positive = trail)
    toe: float = 0.0                      # degrees (positive = toe out)
    scrub_radius: float = 0.02            # m (kingpin offset)

    # === ANTI-ROLL ===
    anti_roll_stiffness: float = 3000.0   # N/m (resists body roll)
    anti_roll_distribution: float = 0.5   # 0=soft, 1=stiff

    # === SUSPENSION TYPE ===
    suspension_type: SuspensionType = SuspensionType.INDEPENDENT

    @property
    def natural_frequency(self) -> float:
        """Natural frequency of spring-mass system (Hz)."""
        # fn = (1/2π) * sqrt(k/m)
        # Assuming 1/4 vehicle mass per corner (~375kg for 1500kg car)
        quarter_mass = 375.0
        return (1 / (2 * pi)) * sqrt(self.spring_rate / quarter_mass)

    @property
    def damping_ratio(self) -> float:
        """Damping ratio (ζ). 1.0 = critically damped, <1 = underdamped."""
        quarter_mass = 375.0
        critical_damping = 2 * sqrt(self.spring_rate * quarter_mass)
        return self.damping_coefficient / critical_damping


@dataclass
class WheelSuspensionState:
    """Runtime state for a single wheel's suspension."""
    compression: float = 0.0              # Current compression (m)
    velocity: float = 0.0                 # Compression velocity (m/s)
    force: float = 0.0                    # Current spring force (N)
    contact: bool = False                 # Ground contact
    contact_point: Vector = field(default_factory=lambda: Vector((0, 0, 0)))

    # Anti-roll state
    roll_moment: float = 0.0

    # Animation outputs
    compression_ratio: float = 0.0        # -1 to +1 (rebound to bump)


# === SUSPENSION PRESETS ===

SUSPENSION_PRESETS = {
    "comfort": SuspensionPhysics(
        spring_rate=28000.0,
        damping_coefficient=2800.0,
        travel=0.18,
        anti_roll_stiffness=1500.0
    ),

    "sport": SuspensionPhysics(
        spring_rate=40000.0,
        damping_coefficient=5000.0,
        travel=0.12,
        anti_roll_stiffness=3500.0,
        camber=-1.5
    ),

    "track": SuspensionPhysics(
        spring_rate=55000.0,
        damping_coefficient=7000.0,
        travel=0.08,
        anti_roll_stiffness=5000.0,
        camber=-2.5,
        caster=7.0
    ),

    "offroad": SuspensionPhysics(
        spring_rate=32000.0,
        damping_coefficient=4500.0,
        travel=0.25,
        anti_roll_stiffness=1000.0,
        progressive_rate=True,
        progressive_factor=1.5
    ),

    "monster": SuspensionPhysics(
        spring_rate=80000.0,
        damping_coefficient=12000.0,
        travel=0.50,
        anti_roll_stiffness=2000.0,
        progressive_rate=True,
        progressive_factor=2.0
    ),

    "lowrider": SuspensionPhysics(
        spring_rate=20000.0,
        damping_coefficient=2000.0,
        travel=0.20,
        anti_roll_stiffness=500.0
    ),

    "stock": SuspensionPhysics(
        spring_rate=35000.0,
        damping_coefficient=4000.0,
        travel=0.15,
        anti_roll_stiffness=3000.0
    ),
}


class SuspensionSystem:
    """
    Full physics-based suspension system.

    Handles:
    - Spring-damper physics simulation
    - Terrain following via raycast
    - Anti-roll bar coupling
    - Bump stop engagement
    """

    def __init__(self):
        self.suspensions: Dict[str, WheelSuspensionState] = {}
        self.gravity = 9.81

    def create_suspension_rig(
        self,
        wheel_pivot: bpy.types.Object,
        config: SuspensionPhysics,
        is_front: bool = True
    ) -> Dict[str, Any]:
        """
        Create physics-based suspension rig for a wheel.

        Args:
            wheel_pivot: Empty object at wheel center
            config: Suspension physics configuration
            is_front: Whether this is a front wheel (affects steering)

        Returns:
            Dictionary with suspension components
        """
        rig = {
            'pivot': wheel_pivot,
            'config': config,
            'is_front': is_front,
            'state': WheelSuspensionState()
        }

        # Store config on pivot for runtime access
        wheel_pivot["suspension_config"] = {
            'spring_rate': config.spring_rate,
            'damping': config.damping_coefficient,
            'travel': config.travel,
            'is_front': is_front
        }

        # Add a suspension arm empty (visual + physics helper)
        arm_name = f"{wheel_pivot.name}_susp_arm"
        arm = bpy.data.objects.new(arm_name, None)
        arm.empty_display_type = 'ARROWS'
        arm.empty_display_size = 0.1
        arm.location = wheel_pivot.location.copy()
        arm.parent = wheel_pivot.parent
        bpy.context.collection.objects.link(arm)

        # Parent wheel pivot to arm
        wheel_pivot.parent = arm

        # Set initial camber (rotation around local X)
        arm.rotation_euler[0] = config.camber * (pi / 180)

        rig['arm'] = arm

        # Track state
        self.suspensions[wheel_pivot.name] = rig['state']

        return rig

    def add_terrain_following(
        self,
        wheel_pivot: bpy.types.Object,
        terrain: bpy.types.Object,
        ray_length: float = 2.0
    ) -> None:
        """
        Add shrinkwrap constraint for terrain following.

        This is a simpler alternative to full physics simulation.
        """
        # Get or create suspension arm
        arm_name = f"{wheel_pivot.name}_susp_arm"
        arm = bpy.data.objects.get(arm_name)

        if not arm:
            return

        # Add shrinkwrap constraint
        if not any(c.type == 'SHRINKWRAP' for c in arm.constraints):
            con = arm.constraints.new('SHRINKWRAP')
            con.target = terrain
            con.shrinkwrap_type = 'PROJECT'
            con.distance = ray_length
            con.project_axis = 'NEG_Z'
            con.use_project_z = True

    def simulate_tick(
        self,
        wheel_pivot: bpy.types.Object,
        terrain_height: float,
        vehicle_velocity: Vector,
        dt: float = 1/24
    ) -> WheelSuspensionState:
        """
        Simulate one tick of suspension physics.

        Uses the spring-damper equation:
        F = -k*x - c*v

        Where x is compression and v is compression velocity.

        Args:
            wheel_pivot: The wheel pivot object
            terrain_height: Height of terrain under wheel
            vehicle_velocity: Vehicle's velocity vector
            dt: Time step in seconds

        Returns:
            Updated suspension state
        """
        config_data = wheel_pivot.get("suspension_config")
        if not config_data:
            return WheelSuspensionState()

        # Get or create state
        if wheel_pivot.name not in self.suspensions:
            self.suspensions[wheel_pivot.name] = WheelSuspensionState()
        state = self.suspensions[wheel_pivot.name]

        # Get configuration
        spring_rate = config_data['spring_rate']
        damping = config_data['damping']
        travel = config_data['travel']

        # Calculate target compression from terrain
        # Wheel position relative to terrain
        wheel_z = wheel_pivot.location.z
        rest_height = wheel_z  # Rest position

        target_compression = rest_height - terrain_height
        target_compression = max(-travel, min(travel, target_compression))

        # Spring-damper physics
        # Current compression error
        compression_error = target_compression - state.compression

        # Calculate force
        # F = -k*(x - x_rest) - c*v
        spring_force = spring_rate * compression_error

        # Progressive spring (gets stiffer as compressed)
        if config_data.get('progressive', False):
            compression_ratio = abs(state.compression / travel)
            stiffness_mult = 1.0 + (compression_ratio * 0.5)
            spring_force *= stiffness_mult

        # Damping force (opposes velocity)
        damping_force = -damping * state.velocity

        # Total force
        total_force = spring_force + damping_force

        # Bump stop (engages near travel limits)
        compression_ratio = state.compression / travel
        if abs(compression_ratio) > 0.85:
            bump_engagement = (abs(compression_ratio) - 0.85) / 0.15
            bump_force = config_data.get('bump_stop', 50000.0) * bump_engagement
            if compression_ratio > 0:
                total_force -= bump_force
            else:
                total_force += bump_force

        # Quarter car mass (approximate)
        quarter_mass = 375.0

        # Calculate acceleration
        acceleration = total_force / quarter_mass

        # Integrate velocity
        state.velocity += acceleration * dt

        # Apply damping to velocity (simple friction model)
        state.velocity *= 0.99

        # Integrate position
        state.compression += state.velocity * dt

        # Clamp to travel limits
        if state.compression > travel:
            state.compression = travel
            state.velocity = 0.0
        elif state.compression < -travel:
            state.compression = -travel
            state.velocity = 0.0

        # Update derived values
        state.force = total_force
        state.compression_ratio = state.compression / travel
        state.contact = terrain_height < rest_height + travel

        # Apply to wheel pivot position (simplified - just Z)
        # In reality, this would be handled by constraints
        arm_name = f"{wheel_pivot.name}_susp_arm"
        arm = bpy.data.objects.get(arm_name)
        if arm:
            arm.location.z = wheel_pivot.parent.location.z - state.compression

        return state

    def apply_anti_roll(
        self,
        left_state: WheelSuspensionState,
        right_state: WheelSuspensionState,
        stiffness: float,
        dt: float = 1/24
    ) -> Tuple[WheelSuspensionState, WheelSuspensionState]:
        """
        Apply anti-roll bar coupling between left and right wheels.

        The anti-roll bar transfers force from the compressed side
        to the extended side, reducing body roll.

        Args:
            left_state: Left wheel suspension state
            right_state: Right wheel suspension state
            stiffness: Anti-roll bar stiffness (N/m)
            dt: Time step

        Returns:
            Updated (left_state, right_state)
        """
        # Difference in compression creates roll moment
        compression_diff = left_state.compression - right_state.compression

        # Anti-roll force (opposes the difference)
        anti_roll_force = stiffness * compression_diff

        # Apply opposing forces
        roll_moment = anti_roll_force * 0.5  # Split between wheels

        # Transfer force from one side to the other
        # This is a simplified model
        quarter_mass = 375.0

        left_state.velocity -= roll_moment / quarter_mass * dt
        right_state.velocity += roll_moment / quarter_mass * dt

        left_state.roll_moment = -roll_moment
        right_state.roll_moment = roll_moment

        return left_state, right_state

    def get_compression_ratio(self, wheel_pivot: bpy.types.Object) -> float:
        """Get current compression ratio (-1 to +1) for a wheel."""
        state = self.suspensions.get(wheel_pivot.name)
        if state:
            return state.compression_ratio
        return 0.0

    def get_all_states(self) -> Dict[str, WheelSuspensionState]:
        """Get all suspension states."""
        return self.suspensions.copy()


def setup_suspension(
    wheel_pivots: List[bpy.types.Object],
    preset: str = "stock",
    front_config: Optional[SuspensionPhysics] = None,
    rear_config: Optional[SuspensionPhysics] = None
) -> SuspensionSystem:
    """
    Convenience function to setup suspension on all wheels.

    Args:
        wheel_pivots: [FL, FR, RL, RR] wheel pivot objects
        preset: Suspension preset name
        front_config: Override front suspension config
        rear_config: Override rear suspension config

    Returns:
        Configured SuspensionSystem instance
    """
    system = SuspensionSystem()

    front = front_config or SUSPENSION_PRESETS.get(preset, SUSPENSION_PRESETS["stock"])
    rear = rear_config or front  # Use same as front if not specified

    for i, pivot in enumerate(wheel_pivots):
        if pivot is None:
            continue

        is_front = i < 2
        config = front if is_front else rear
        system.create_suspension_rig(pivot, config, is_front)

    return system


def get_suspension_preset(preset_name: str) -> SuspensionPhysics:
    """Get a suspension preset by name."""
    return SUSPENSION_PRESETS.get(preset_name, SUSPENSION_PRESETS["stock"])


def list_suspension_presets() -> List[str]:
    """List available suspension presets."""
    return list(SUSPENSION_PRESETS.keys())
