# Procedural Car Augmentations - Master Plan

**Vision**: Cartoon-style cars that move with real physics, from background traffic to hero vehicles to mutant wasteland monsters.

---

## The Hierarchy: Reality-Based Foundation

```
┌─────────────────────────────────────────────────────────────┐
│                    VEHICLE CLASSES                          │
├─────────────────────────────────────────────────────────────┤
│  HERO CAR      │ Full interior, physics, damage, detail    │
│  FEATURE CAR   │ Interior visible, physics, limited damage │
│  TRAFFIC CAR   │ Basic interior, simplified physics        │
│  BACKGROUND    │ Shell only, follow-path physics           │
└─────────────────────────────────────────────────────────────┘

All classes share the same physics foundation - detail varies.
```

---

## Phase 1: Physics Foundation (The Reality Layer)

**Goal**: Every car moves like a real car, regardless of visual style.

### 1.1 Rigid Body Physics Core
```python
# lib/animation/vehicle/physics_core.py

@dataclass
class VehiclePhysics:
    """Real-world physics parameters for vehicle simulation."""
    mass: float = 1500.0              # kg
    mass_distribution: Tuple[float, float, float] = (0.5, 0.5, 0.3)  # front/rear/center
    center_of_gravity: Vector = field(default_factory=lambda: Vector((0, 0, 0.4)))

    # Aerodynamics
    drag_coefficient: float = 0.32
    frontal_area: float = 2.2         # m²
    downforce_coefficient: float = 0.1

    # Engine/Power
    max_power: float = 150.0          # kW (200 hp)
    max_torque: float = 300.0         # Nm
    redline_rpm: float = 6500.0

    # Transmission
    gear_ratios: List[float] = field(default_factory=lambda: [3.5, 2.1, 1.4, 1.0, 0.8])
    final_drive: float = 3.7
    drivetrain_efficiency: float = 0.9

    # Brakes
    brake_bias: float = 0.6           # Front bias
    max_brake_torque: float = 3000.0  # Nm per wheel

    # Tires
    tire_grip_front: float = 1.0
    tire_grip_rear: float = 1.0
    tire_radius: float = 0.35
    tire_width: float = 0.225

class PhysicsEngine:
    """Blender physics integration for vehicles."""

    def setup_rigid_body(self, vehicle: bpy.types.Object, physics: VehiclePhysics):
        """Configure rigid body with proper mass distribution."""
        ...

    def create_wheel_constraints(self, vehicle: bpy.types.Object, wheels: List[WheelConfig]):
        """Create hinge constraints for wheels with suspension."""
        ...

    def apply_engine_force(self, vehicle: bpy.types.Object, throttle: float, gear: int):
        """Apply driving force through driven wheels."""
        ...

    def apply_braking(self, vehicle: bpy.types.Object, brake_amount: float):
        """Apply braking force with proper bias."""
        ...
```

### 1.2 Suspension System (Real Physics)
```python
# lib/animation/vehicle/suspension.py

@dataclass
class SuspensionPhysics:
    """Spring-damper suspension parameters."""
    spring_rate: float = 35000.0      # N/m
    damping_coefficient: float = 4000.0  # Ns/m
    travel: float = 0.15              # m (150mm)
    anti_roll_bar: float = 3000.0     # N/m
    bump_stop_force: float = 50000.0  # N

    # Geometry
    camber: float = -0.5              # degrees (negative = top in)
    caster: float = 5.0               # degrees
    toe: float = 0.0                  # degrees

class SuspensionSystem:
    """Full physics-based suspension with spring-damper model."""

    def create_suspension_rig(self, wheel_pivot: bpy.types.Object, config: SuspensionPhysics):
        """Create physics-based suspension with:
        - Spring constraint (damped spring)
        - Travel limits
        - Anti-roll linkage
        """
        ...

    def add_terrain_following(self, suspension, terrain: bpy.types.Object):
        """Raycast-based terrain following."""
        ...

    def simulate_compression(self, suspension, impact_force: float) -> float:
        """Calculate and apply suspension compression."""
        ...
```

### 1.3 Tire Physics
```python
# lib/animation/vehicle/tire_physics.py

@dataclass
class TirePhysics:
    """Pacejka tire model parameters (Magic Formula)."""
    # Longitudinal
    b0_long: float = 1.65
    b1_long: float = 0.0
    b2_long: float = 1688.0
    b3_long: float = 0.0
    b4_long: float = 229.0

    # Lateral
    a0_lat: float = 1.65
    a1_lat: float = 0.0
    a2_lat: float = 1688.0

    # Slip ratios
    optimal_slip_ratio: float = 0.1   # 10% slip for peak force

class TireSystem:
    """Realistic tire physics with slip and grip."""

    def calculate_slip(self, wheel_speed: float, vehicle_speed: float) -> float:
        """Calculate slip ratio (0 = rolling, 1 = locked)."""
        ...

    def calculate_lateral_force(self, slip_angle: float, normal_force: float) -> float:
        """Pacejka magic formula for cornering force."""
        ...

    def calculate_longitudinal_force(self, slip_ratio: float, normal_force: float) -> float:
        """Pacejka formula for acceleration/braking force."""
        ...
```

---

## Phase 2: Interior System (Steering to Tires)

**Goal**: Visible interiors with functional steering-wheel-to-tire connection.

### 2.1 Interior Architecture
```python
# lib/animation/vehicle/interior.py

@dataclass
class InteriorConfig:
    """Interior detail level and components."""
    detail_level: str = "hero"  # hero, feature, traffic, none

    # Components
    steering_wheel: bool = True
    dashboard: bool = True
    seats: bool = True
    rear_view_mirror: bool = True
    gear_shifter: bool = True
    pedals: bool = True
    speedometer: bool = True

    # Visibility
    window_tint: float = 0.3    # 0=clear, 1=blackout

class InteriorFactory:
    """Create procedural interiors for cars."""

    def create_interior(self, vehicle: bpy.types.Object, config: InteriorConfig):
        """Generate interior based on detail level."""
        if config.detail_level == "hero":
            return self._create_hero_interior(vehicle, config)
        elif config.detail_level == "feature":
            return self._create_feature_interior(vehicle, config)
        else:
            return self._create_traffic_interior(vehicle, config)

    def _create_hero_interior(self, vehicle, config):
        """Full interior with all details:
        - Detailed steering wheel with animated rotation
        - Dashboard with instruments
        - Seats with headrests
        - Pedals (gas, brake, clutch)
        - Gear shifter
        """
        ...

    def connect_steering_to_wheels(self, steering_wheel: bpy.types.Object,
                                    front_wheels: List[bpy.types.Object],
                                    ratio: float = 15.0):
        """Create driver constraint: steering wheel rotation -> wheel steering.

        Ratio: steering wheel turns 15:1 to wheel angle
        (540° steering wheel = 36° wheel angle)
        """
        # Add driver to front wheel pivots
        # Expression: steering_wheel.rotation_euler[2] / ratio
        ...
```

### 2.2 Steering Column Rig
```python
# lib/animation/vehicle/steering_column.py

class SteeringColumn:
    """Animated steering column connecting wheel to tires."""

    def create_column(self, vehicle: bpy.types.Object) -> bpy.types.Object:
        """Create steering column bone/empty chain:
        - steering_wheel_empty (rotates)
        - column_shaft (visual)
        - rack_pinion (converts rotation to lateral)
        """
        ...

    def add_steering_driver(self, steering_wheel: bpy.types.Object,
                            path_curve: bpy.types.Curve,
                            look_ahead: float = 5.0):
        """Auto-steer based on path curvature.

        Look ahead determines how early the wheel turns before corners.
        """
        ...

    def add_manual_control(self, steering_wheel: bpy.types.Object,
                           controller: bpy.types.Object):
        """Connect to control empty for manual steering animation."""
        ...
```

---

## Phase 3: Weathering & Wear System

**Goal**: Cars show age, use, and environmental exposure.

### 3.1 Weathering Layers
```python
# lib/animation/vehicle/weathering.py

@dataclass
class WeatheringConfig:
    """Weathering and wear parameters."""
    # Age
    age_years: float = 5.0

    # Dirt
    dirt_level: float = 0.3          # 0-1
    dirt_accumulation: str = "realistic"  # realistic, heavy, light
    mud_splatter: bool = True
    dust_coating: bool = True

    # Paint
    sun_fade: float = 0.2            # 0-1
    clear_coat_wear: float = 0.1
    scratches: int = 5
    chips: int = 10
    rust_spots: int = 0

    # Wear patterns
    door_dings: int = 3
    bumper_scuffs: bool = True
    wheel_well_grime: bool = True

class WeatheringSystem:
    """Apply procedural weathering to vehicles."""

    def apply_weathering(self, vehicle: bpy.types.Object, config: WeatheringConfig):
        """Apply all weathering effects via:
        - Vertex colors for dirt maps
        - Material node mixing
        - Decal projection for scratches
        """
        ...

    def generate_dirt_mask(self, vehicle: bpy.types.Object,
                           accumulation_points: List[Vector]) -> bpy.types.Image:
        """Generate dirt accumulation texture based on:
        - Aerodynamic flow (less dirt on leading edges)
        - Water drainage paths
        - Wheel well spray zones
        """
        ...

    def add_rust(self, vehicle: bpy.types.Object, spots: int, severity: float):
        """Add rust spots with:
        - Color variation
        - Surface pitting (displacement)
        - Edge bleeding
        """
        ...

    def add_scratches(self, vehicle: bpy.types.Object, count: int,
                      depth: float = 0.001):
        """Add procedural scratches:
        - Directional (horizontal for parking lot scrapes)
        - Random depth
        - Primer color underneath
        """
        ...
```

### 3.2 Hero vs Traffic Weathering
```python
# presets

HERO_WEATHERING = WeatheringConfig(
    dirt_level=0.1,
    sun_fade=0.05,
    scratches=2,
    chips=3,
    mud_splatter=False
)

TRAFFIC_WEATHERING = WeatheringConfig(
    dirt_level=0.3,
    sun_fade=0.2,
    scratches=8,
    chips=15,
    mud_splatter=True
)

WASTELAND_WEATHERING = WeatheringConfig(
    dirt_level=0.7,
    sun_fade=0.4,
    scratches=20,
    chips=30,
    rust_spots=15,
    mud_splatter=True,
    bumper_scuffs=True,
    clear_coat_wear=0.8
)
```

---

## Phase 4: Damage & Deformation

**Goal**: Realistic crash damage and deformation.

### 4.1 Damage System
```python
# lib/animation/vehicle/damage.py

@dataclass
class DamageZone:
    """Crumple zone configuration."""
    name: str
    vertices: List[int]              # Vertex indices
    stiffness: float = 1.0           # Resistance to deformation
    max_deformation: float = 0.3     # Maximum displacement (fraction)
    detachable: bool = False
    detach_force: float = 50000.0    # Force threshold for detachment

@dataclass
class DamageConfig:
    """Vehicle damage configuration."""
    zones: List[DamageZone] = field(default_factory=list)
    glass_shatter: bool = True
    detachable_parts: List[str] = field(default_factory=lambda: [
        "bumper_front", "bumper_rear", "mirror_left", "mirror_right",
        "door_left", "door_right", "hood", "trunk"
    ])
    deformation_style: str = "realistic"  # realistic, cartoon, extreme

class DamageSystem:
    """Physics-based damage and deformation."""

    def setup_crumple_zones(self, vehicle: bpy.types.Object, config: DamageConfig):
        """Define crumple zones for physics-based deformation."""
        ...

    def apply_impact(self, vehicle: bpy.types.Object,
                     impact_point: Vector,
                     impact_force: Vector,
                     impact_radius: float):
        """Apply impact damage:
        1. Calculate force distribution
        2. Deform nearby vertices
        3. Check for part detachment
        4. Spawn debris particles
        """
        ...

    def shatter_glass(self, vehicle: bpy.types.Object, window: str):
        """Shatter a window:
        - Create fracture pieces
        - Apply physics to shards
        - Play glass sound
        """
        ...

    def detach_part(self, vehicle: bpy.types.Object, part_name: str):
        """Detach a part from the vehicle:
        - Separate mesh or collection instance
        - Add rigid body physics
        - Inherit vehicle velocity
        """
        ...
```

### 4.2 Visual Damage States
```python
# lib/animation/vehicle/damage_states.py

class DamageStates:
    """Manage visual damage progression."""

    # Damage levels: 0 (pristine) to 1 (destroyed)
    def set_damage_level(self, vehicle: bpy.types.Object, level: float):
        """Set overall damage level:
        - 0.0: Pristine
        - 0.2: Minor (scratches, small dents)
        - 0.4: Moderate (dents, cracked glass)
        - 0.6: Severe (major deformation, missing parts)
        - 0.8: Critical (barely functional)
        - 1.0: Destroyed
        """
        ...

    def get_damage_state_name(self, level: float) -> str:
        mapping = {
            (0.0, 0.1): "pristine",
            (0.1, 0.3): "minor_damage",
            (0.3, 0.5): "moderate_damage",
            (0.5, 0.7): "severe_damage",
            (0.7, 0.9): "critical_damage",
            (0.9, 1.0): "destroyed"
        }
        ...
```

---

## Phase 5: Mutant/Monster Cars (Mad Max Style)

**Goal**: Extreme customization - monster truck chassis + any body.

### 5.1 Monster Components
```python
# lib/animation/vehicle/monster_factory.py

@dataclass
class MonsterConfig:
    """Configuration for mutant/monster vehicles."""
    # Chassis
    chassis_type: str = "monster_truck"  # stock, lifted, monster, baja
    lift_height: float = 0.0             # meters above stock

    # Tires
    tire_type: str = "monster"           # stock, offroad, mud, monster
    tire_size_multiplier: float = 1.0

    # Armor
    armor_plating: bool = False
    armor_coverage: float = 0.5          # 0-1
    spikes: bool = False
    spike_count: int = 10

    # Weapons (visual)
    ram_bars: bool = False
    spinning_blades: bool = False
    flamethrower: bool = False

    # Style
    rust_level: float = 0.5
    improvised_repairs: bool = True      # Duct tape, wire, patches
    scrap_armor: bool = False            # Random metal plates

class MonsterFactory:
    """Create mutant wasteland vehicles."""

    def create_monster_car(
        self,
        base_style: str = "sedan",      # Any body style
        config: MonsterConfig = None
    ) -> bpy.types.Object:
        """Create a monster version of any car:
        1. Start with procedural car body
        2. Apply monster chassis (lifted suspension)
        3. Add giant tires
        4. Apply armor/weaponry
        5. Add wasteland weathering
        """
        ...

    def apply_monster_chassis(self, vehicle: bpy.types.Object, lift: float):
        """Replace stock chassis with monster truck frame:
        - Extended suspension travel
        - Heavy-duty driveshafts
        - Visible chassis rails
        """
        ...

    def add_monster_tires(self, vehicle: bpy.types.Object, size: float):
        """Add oversized monster truck tires:
        - Custom tire mesh (aggressive tread)
        - Extended wheel hubs
        - Tire wobble at low speeds
        """
        ...

    def add_armor(self, vehicle: bpy.types.Object, coverage: float):
        """Add improvised armor plating:
        - Random metal plates
        - Welded seams
        - Rust and paint mismatch
        """
        ...

    def add_weapons(self, vehicle: bpy.types.Object, config: MonsterConfig):
        """Add visual weapons (non-functional, just aesthetic):
        - Front ram bars
        - Side spinning blades (animated)
        - Rear flamethrower (particle system)
        """
        ...
```

### 5.2 Chassis Swapping System
```python
# lib/animation/vehicle/chassis_swap.py

class ChassisSwapper:
    """Swap any car body onto different chassis."""

    CHASSIS_TYPES = {
        "stock": ChassisConfig(
            ride_height=0.15,
            suspension_travel=0.15,
            tire_size=0.35
        ),
        "lifted": ChassisConfig(
            ride_height=0.30,
            suspension_travel=0.20,
            tire_size=0.40
        ),
        "monster": ChassisConfig(
            ride_height=0.60,
            suspension_travel=0.40,
            tire_size=0.85
        ),
        "lowrider": ChassisConfig(
            ride_height=0.08,
            suspension_travel=0.10,
            tire_size=0.30,
            bounce=True
        ),
        "baja": ChassisConfig(
            ride_height=0.35,
            suspension_travel=0.35,
            tire_size=0.45,
            long_travel=True
        )
    }

    def swap_chassis(self, vehicle: bpy.types.Object, chassis_type: str):
        """Swap the chassis while keeping the body:
        1. Store body geometry
        2. Remove existing chassis/suspension
        3. Create new chassis
        4. Reattach body at new height
        5. Update wheel positions
        6. Recalibrate physics
        """
        ...
```

---

## Phase 6: Animation Hooks

**Goal**: Animation-ready outputs for every system.

### 6.1 Animation Controller
```python
# lib/animation/vehicle/animation_hooks.py

@dataclass
class AnimationHooks:
    """Animation-ready outputs from vehicle systems."""

    # Wheel outputs
    wheel_rotation: List[float] = field(default_factory=list)  # Per wheel
    wheel_spin_rate: List[float] = field(default_factory=list)  # For smoke

    # Steering outputs
    steering_angle: float = 0.0
    steering_wheel_rotation: float = 0.0

    # Suspension outputs
    suspension_compression: List[float] = field(default_factory=list)

    # Engine outputs
    rpm: float = 0.0
    gear: int = 1
    throttle: float = 0.0
    brake: float = 0.0

    # Damage outputs
    damage_level: float = 0.0
    detached_parts: List[str] = field(default_factory=list)

    # Effects outputs
    exhaust_smoke_intensity: float = 0.0
    tire_smoke_intensity: List[float] = field(default_factory=list)
    spark_locations: List[Vector] = field(default_factory=list)

class AnimationController:
    """Drive animation from physics simulation."""

    def create_animation_outputs(self, vehicle: bpy.types.Object):
        """Create custom properties for all animation hooks."""
        ...

    def export_to_alembic(self, vehicles: List[bpy.types.Object], filepath: str):
        """Export animation to Alembic for external rendering."""
        ...

    def generate_audio_markers(self, vehicle: bpy.types.Object) -> List[Dict]:
        """Generate audio sync markers:
        - Engine rev points
        - Tire squeal events
        - Crash impacts
        - Horn honks
        """
        ...
```

---

## Implementation Priority

### Phase 1 (Foundation) - Week 1
- [ ] Physics core with rigid body setup
- [ ] Suspension system (spring-damper)
- [ ] Tire physics (slip/grip)
- [ ] Basic interior with steering-wheel-to-tires

### Phase 2 (Detail) - Week 2
- [ ] Full interior system (hero/feature/traffic)
- [ ] Weathering system
- [ ] Animation hooks

### Phase 3 (Advanced) - Week 3
- [ ] Damage and deformation
- [ ] Monster car factory
- [ ] Chassis swapping

### Phase 4 (Polish) - Week 4
- [ ] Particle effects (smoke, sparks)
- [ ] Audio markers
- [ ] Testing and documentation

---

## File Structure

```
lib/animation/vehicle/
├── __init__.py
├── physics_core.py          # 🆕 Real physics engine
├── suspension.py            # Updated with spring-damper
├── tire_physics.py          # 🆕 Pacejka tire model
├── interior.py              # 🆕 Procedural interiors
├── steering_column.py       # 🆕 Steering rig
├── weathering.py            # 🆕 Dirt/rust/scratches
├── damage.py                # 🆕 Crumple zones
├── damage_states.py         # 🆕 Visual damage levels
├── monster_factory.py       # 🆕 Mad Max style cars
├── chassis_swap.py          # 🆕 Chassis swapping
├── animation_hooks.py       # 🆕 Animation outputs
├── procedural_car.py        # Updated to use physics
├── car_styling.py           # Updated with weathering
├── launch_control.py
├── stunt_coordinator.py
└── driver_system.py

configs/animation/vehicle/
├── physics/                 # 🆕 Physics presets
│   ├── sedan_physics.yaml
│   ├── sports_physics.yaml
│   ├── truck_physics.yaml
│   └── monster_physics.yaml
├── interiors/               # 🆕 Interior presets
│   ├── hero.yaml
│   ├── feature.yaml
│   └── traffic.yaml
└── weathering/              # 🆕 Weathering presets
    ├── pristine.yaml
    ├── daily_driver.yaml
    ├── worn.yaml
    └── wasteland.yaml
```
