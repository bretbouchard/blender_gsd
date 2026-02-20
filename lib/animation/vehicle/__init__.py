"""
Vehicle Animation Module - Complete System

A comprehensive vehicle animation and physics system for Blender 5.x.
From procedural cars to monster trucks, with real physics.

## Phases

**Phase 1: Physics Foundation**
- VehiclePhysics: Real-world physics parameters
- PhysicsEngine: Rigid body setup and force application
- SuspensionSystem: Spring-damper suspension
- TirePhysics: Pacejka Magic Formula tire model

**Phase 2: Interior & Steering**
- InteriorFactory: Procedural interiors (hero/feature/traffic)
- SteeringColumn: Steering wheel to tire connection

**Phase 3: Weathering**
- WeatheringSystem: Dirt, rust, scratches, wear

**Phase 4: Damage**
- DamageSystem: Crumple zones, detachable parts

**Phase 5: Monster Vehicles**
- MonsterFactory: Mad Max style wasteland vehicles
- ChassisSwapper: Put any body on any chassis

**Phase 6: Animation**
- AnimationHooks: Connect physics to animation
- AnimationController: State tracking and output

## Quick Start

```python
# Create a procedural car
from lib.animation.vehicle import create_car
car = create_car(style="sports", color="red")

# Create a monster truck
from lib.animation.vehicle import create_monster_car
monster = create_monster_car(base_style="pickup", preset="apocalypse")

# Setup physics
from lib.animation.vehicle import setup_vehicle_physics
engine, physics = setup_vehicle_physics(car, preset="sports")

# Apply weathering
from lib.animation.vehicle import apply_weathering
apply_weathering(car, preset="daily_driver")

# Setup animation
from lib.animation.vehicle import setup_animation_hooks
hooks = setup_animation_hooks(car)
```
"""

# === ORIGINAL MODULES ===

from .wheel_system import (
    WheelSystem,
    setup_car_wheels,
)

from .suspension import (
    SuspensionSystem,
    setup_vehicle_suspension,
)

from .plugin_interface import (
    VehiclePluginInterface,
    BlenderPhysicsVehicle,
    get_plugin,
    get_available_plugins,
    is_plugin_available,
)

from .vehicle_config import (
    VehicleConfigManager,
    load_vehicle_config,
    save_vehicle_config,
    list_vehicle_configs,
    validate_vehicle_config,
    create_default_vehicle_config,
)

from .launch_control import (
    LaunchController,
    create_launch_controller,
)

from .stunt_coordinator import (
    StuntCoordinator,
    StuntMarker,
    create_stunt_coordinator,
)

from .driver_system import (
    ExpertDriver,
    get_driver_profile,
    DRIVER_PRESETS,
)

# === NEW AUGMENTATION MODULES ===

# Phase 1: Physics Core
from .physics_core import (
    VehiclePhysics,
    PhysicsEngine,
    PhysicsState,
    DrivetrainType,
    PHYSICS_PRESETS,
    setup_vehicle_physics,
    get_physics_preset,
    list_physics_presets,
)

# Phase 1: Suspension Physics
from .suspension_physics import (
    SuspensionPhysics,
    SuspensionSystem as SuspensionPhysicsSystem,
    WheelSuspensionState,
    SuspensionType,
    SUSPENSION_PRESETS,
    setup_suspension,
    get_suspension_preset,
    list_suspension_presets,
)

# Phase 1: Tire Physics
from .tire_physics import (
    TirePhysics,
    TireSystem,
    WheelTireState,
    TireType,
    TireCondition,
    TIRE_PRESETS,
    calculate_tire_forces,
    get_tire_preset,
    list_tire_presets,
)

# Phase 2: Interior
from .interior import (
    InteriorConfig,
    InteriorFactory,
    InteriorDetailLevel,
    INTERIOR_PRESETS,
    create_interior,
    get_interior_preset,
    list_interior_presets,
)

# Phase 2: Steering
from .steering import (
    SteeringConfig,
    SteeringColumn,
    SteeringStyle,
    STEERING_PRESETS,
    setup_steering,
    calculate_ackermann_angles,
    get_steering_preset,
    list_steering_presets,
)

# Phase 3: Weathering
from .weathering import (
    WeatheringConfig,
    WeatheringSystem,
    DirtPattern,
    RustSeverity,
    WEATHERING_PRESETS,
    apply_weathering,
    get_weathering_preset,
    list_weathering_presets,
)

# Phase 4: Damage
from .damage import (
    DamageConfig,
    DamageZone,
    DamageSystem,
    DamageState,
    DamageType,
    DamageSeverity,
    DAMAGE_PRESETS,
    apply_impact_damage,
    get_damage_preset,
    list_damage_presets,
)

# Phase 5: Monster Factory
from .monster_factory import (
    MonsterConfig,
    MonsterFactory,
    ChassisType as MonsterChassisType,
    TireSize,
    ArmorStyle,
    MONSTER_PRESETS,
    create_monster_car,
    get_monster_preset,
    list_monster_presets,
)

# Phase 5: Chassis Swap
from .chassis_swap import (
    ChassisSwapper,
    ChassisConfig,
    ChassisType,
    CHASSIS_PRESETS,
    swap_chassis,
    list_chassis_types,
    get_chassis_config,
)

# Phase 6: Animation Hooks
from .animation_hooks import (
    AnimationHooks,
    AnimationController,
    AnimationState,
    AudioMarker,
    setup_animation_hooks,
    get_animation_state,
)

# Procedural Car (existing, updated)
from .procedural_car import (
    CarStyle,
    CarColors,
    ProceduralCarFactory,
    STYLE_PRESETS,
    COLOR_PRESETS,
    create_car,
    create_fleet,
)

# Car Styling (existing)
from .car_styling import (
    BodyProportions,
    ColorScheme,
    PartSelection,
    DetailLevel,
    Weathering,
    CarStyler,
    style_car,
)


__all__ = [
    # === ORIGINAL ===
    # Wheel system
    'WheelSystem',
    'setup_car_wheels',

    # Suspension (original)
    'SuspensionSystem',
    'setup_vehicle_suspension',

    # Plugin interface
    'VehiclePluginInterface',
    'BlenderPhysicsVehicle',
    'get_plugin',
    'get_available_plugins',
    'is_plugin_available',

    # Configuration
    'VehicleConfigManager',
    'load_vehicle_config',
    'save_vehicle_config',
    'list_vehicle_configs',
    'validate_vehicle_config',
    'create_default_vehicle_config',

    # Launch control
    'LaunchController',
    'create_launch_controller',

    # Stunt coordination
    'StuntCoordinator',
    'StuntMarker',
    'create_stunt_coordinator',

    # Driver system
    'ExpertDriver',
    'get_driver_profile',
    'DRIVER_PRESETS',

    # === PHASE 1: PHYSICS ===
    'VehiclePhysics',
    'PhysicsEngine',
    'PhysicsState',
    'DrivetrainType',
    'PHYSICS_PRESETS',
    'setup_vehicle_physics',
    'get_physics_preset',
    'list_physics_presets',

    'SuspensionPhysics',
    'SuspensionPhysicsSystem',
    'WheelSuspensionState',
    'SuspensionType',
    'SUSPENSION_PRESETS',
    'setup_suspension',
    'get_suspension_preset',
    'list_suspension_presets',

    'TirePhysics',
    'TireSystem',
    'WheelTireState',
    'TireType',
    'TireCondition',
    'TIRE_PRESETS',
    'calculate_tire_forces',
    'get_tire_preset',
    'list_tire_presets',

    # === PHASE 2: INTERIOR & STEERING ===
    'InteriorConfig',
    'InteriorFactory',
    'InteriorDetailLevel',
    'INTERIOR_PRESETS',
    'create_interior',
    'get_interior_preset',
    'list_interior_presets',

    'SteeringConfig',
    'SteeringColumn',
    'SteeringStyle',
    'STEERING_PRESETS',
    'setup_steering',
    'calculate_ackermann_angles',
    'get_steering_preset',
    'list_steering_presets',

    # === PHASE 3: WEATHERING ===
    'WeatheringConfig',
    'WeatheringSystem',
    'DirtPattern',
    'RustSeverity',
    'WEATHERING_PRESETS',
    'apply_weathering',
    'get_weathering_preset',
    'list_weathering_presets',

    # === PHASE 4: DAMAGE ===
    'DamageConfig',
    'DamageZone',
    'DamageSystem',
    'DamageState',
    'DamageType',
    'DamageSeverity',
    'DAMAGE_PRESETS',
    'apply_impact_damage',
    'get_damage_preset',
    'list_damage_presets',

    # === PHASE 5: MONSTER & CHASSIS ===
    'MonsterConfig',
    'MonsterFactory',
    'MonsterChassisType',
    'TireSize',
    'ArmorStyle',
    'MONSTER_PRESETS',
    'create_monster_car',
    'get_monster_preset',
    'list_monster_presets',

    'ChassisSwapper',
    'ChassisConfig',
    'ChassisType',
    'CHASSIS_PRESETS',
    'swap_chassis',
    'list_chassis_types',
    'get_chassis_config',

    # === PHASE 6: ANIMATION ===
    'AnimationHooks',
    'AnimationController',
    'AnimationState',
    'AudioMarker',
    'setup_animation_hooks',
    'get_animation_state',

    # === PROCEDURAL CAR ===
    'CarStyle',
    'CarColors',
    'ProceduralCarFactory',
    'STYLE_PRESETS',
    'COLOR_PRESETS',
    'create_car',
    'create_fleet',

    # === CAR STYLING ===
    'BodyProportions',
    'ColorScheme',
    'PartSelection',
    'DetailLevel',
    'Weathering',
    'CarStyler',
    'style_car',
]
