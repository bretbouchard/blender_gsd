"""
Launch Control - Vehicle Rigging System

A comprehensive one-click vehicle rigging system with suspension physics,
steering, and animation capabilities for Blender.

Modules:
- auto_rig: One-click rigging with automatic component detection
- suspension: Physics-based suspension simulation
- steering: Vehicle steering with Ackermann geometry
- physics: Vehicle physics and movement simulation
- ground_detection: Terrain interaction system
- presets: Pre-built animation presets
- export: FBX/GLTF export utilities

Quick Start:
    from lib.vehicle.launch_control import (
        LaunchControlRig, WheelDetector,
        SuspensionSystem, DampingCurve,
        SteeringSystem, AckermannGeometry,
        VehiclePhysics, SpeedSegments,
        GroundDetection, AnimationPresets,
        VehicleExporter,
    )

    # One-click rig setup
    rig = LaunchControlRig(vehicle_body)
    rig.one_click_rig()

    # Configure suspension
    suspension = SuspensionSystem(rig)
    suspension.configure(travel=0.3, spring_stiffness=25000)
    suspension.enable_physics()

    # Setup steering
    steering = SteeringSystem(rig)
    steering.configure(max_angle=35.0, ackermann=True)
    steering.create_controller()

    # Physics simulation
    physics = VehiclePhysics(rig)
    physics.configure(mass=1500, engine_power=150000)
    physics.drive_path(path_curve, speed=15.0)

    # Ground detection
    ground = GroundDetection(rig)
    ground.set_ground_object(terrain_mesh)
    ground.enable_auto_height()

    # Apply animation preset
    AnimationPresets.drift_donut(rig, duration=120, direction="left")

    # Export
    VehicleExporter.export_fbx("/path/to/output.fbx", rig)
"""

from typing import TYPE_CHECKING

# Auto-rigging system
from .auto_rig import (
    LaunchControlRig,
    WheelDetector,
    ComponentDetectionResult,
    RigConfiguration,
    SuspensionType,
    SteeringType,
)

# Suspension physics
from .suspension import (
    SuspensionSystem,
    DampingCurve,
    SuspensionConfig,
    DampingMode,
    PhysicsMode,
    WheelSpringData,
)

# Steering system
from .steering import (
    SteeringSystem,
    AckermannGeometry,
    SteeringConfig,
    SteeringControllerType,
    AckermannResult,
)

# Vehicle physics
from .physics import (
    VehiclePhysics,
    SpeedSegments,
    PhysicsConfig,
    SpeedSegment,
    DriftConfig,
    JumpConfig,
    OffroadConfig,
)

# Ground detection
from .ground_detection import (
    GroundDetection,
    GroundConfig,
    SurfaceInfo,
    ContactPoint,
    SurfaceType,
)

# Animation presets
from .presets import (
    AnimationPresets,
    PresetConfig,
    DriftDonutConfig,
    FigureEightConfig,
    SlalomConfig,
    JumpRampConfig,
    OffroadBounceConfig,
    EmergencyBrakeConfig,
    AccelerationSquatConfig,
)

# Export utilities
from .export import (
    VehicleExporter,
    ExportConfig,
    BakeOptions,
    ExportFormat,
)

# Vehicle paths (road network integration)
from .vehicle_paths import (
    VehiclePathSystem,
    VehiclePath,
    SpeedCurve,
    PathType,
    SpeedSegmentAdapter,
)

# Stunt driving presets
from .stunts import (
    StuntPresets,
    StuntType,
    BarrelRollConfig,
    JTurnConfig,
    BootlegConfig,
    TwoWheelConfig,
    ChaseSequenceConfig,
)

# HUD system
from .hud import (
    HUDSystem,
    HUDConfig,
    HUDMode,
    TelemetryData,
    HUDWidget,
    WidgetType,
    SteeringWidget,
    SpeedometerWidget,
    GearWidget,
    GForceWidget,
    HUD_PRESETS,
    create_vehicle_hud,
    get_hud_presets,
)

# Asset processor
from .asset_processor import (
    CarDetector,
    CarDetectionResult,
    LaunchControlBuilder,
    process_blend_file,
    process_current_scene,
    process_supercars_assets,
)


__all__ = [
    # Auto-rigging
    "LaunchControlRig",
    "WheelDetector",
    "ComponentDetectionResult",
    "RigConfiguration",
    "SuspensionType",
    "SteeringType",
    # Suspension
    "SuspensionSystem",
    "DampingCurve",
    "SuspensionConfig",
    "DampingMode",
    "PhysicsMode",
    "WheelSpringData",
    # Steering
    "SteeringSystem",
    "AckermannGeometry",
    "SteeringConfig",
    "SteeringControllerType",
    "AckermannResult",
    # Physics
    "VehiclePhysics",
    "SpeedSegments",
    "PhysicsConfig",
    "SpeedSegment",
    "DriftConfig",
    "JumpConfig",
    "OffroadConfig",
    # Ground detection
    "GroundDetection",
    "GroundConfig",
    "SurfaceInfo",
    "ContactPoint",
    "SurfaceType",
    # Presets
    "AnimationPresets",
    "PresetConfig",
    "DriftDonutConfig",
    "FigureEightConfig",
    "SlalomConfig",
    "JumpRampConfig",
    "OffroadBounceConfig",
    "EmergencyBrakeConfig",
    "AccelerationSquatConfig",
    # Export
    "VehicleExporter",
    "ExportConfig",
    "BakeOptions",
    "ExportFormat",
    # Vehicle paths
    "VehiclePathSystem",
    "VehiclePath",
    "SpeedCurve",
    "PathType",
    "SpeedSegmentAdapter",
    # Stunts
    "StuntPresets",
    "StuntType",
    "BarrelRollConfig",
    "JTurnConfig",
    "BootlegConfig",
    "TwoWheelConfig",
    "ChaseSequenceConfig",
    # HUD
    "HUDSystem",
    "HUDConfig",
    "HUDMode",
    "TelemetryData",
    "HUDWidget",
    "WidgetType",
    "SteeringWidget",
    "SpeedometerWidget",
    "GearWidget",
    "GForceWidget",
    "HUD_PRESETS",
    "create_vehicle_hud",
    "get_hud_presets",
    # Asset processor
    "CarDetector",
    "CarDetectionResult",
    "LaunchControlBuilder",
    "process_blend_file",
    "process_current_scene",
    "process_supercars_assets",
]

__version__ = "0.1.0"

# Lazy imports for Blender API compatibility
if TYPE_CHECKING:
    import bpy
    from mathutils import Vector, Matrix, Quaternion
