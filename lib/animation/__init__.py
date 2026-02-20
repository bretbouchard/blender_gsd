"""
Animation System for Blender GSD

Provides rigging, IK/FK, posing, blocking, and animation tools.

Phase 13.0: Rigging Foundation (REQ-ANIM-01)
Phase 13.1: IK/FK System (REQ-ANIM-02, REQ-ANIM-03)

Usage:
    from lib.animation import (
        RigConfig, RigBuilder, build_rig_from_preset,
        auto_weight_mesh, list_available_presets,
        IKSystem, FKSystem, IKFKBlender
    )

    # Build a rig from preset
    armature = build_rig_from_preset("human_biped")

    # Auto-weight a mesh
    auto_weight_mesh(armature, my_mesh)

    # Setup IK on a limb
    ik_system = IKSystem(armature)
    ik_system.add_ik_constraint(armature, ik_config)

    # Blend between IK and FK
    blender = IKFKBlender(armature, blend_config)
    blender.set_blend_factor(0.5)  # 50% IK, 50% FK
"""

# Types
from .types import (
    # Enums
    RigType,
    BoneGroupType,
    WeightMethod,
    IKMode,
    RotationOrder,
    BlendMode,
    # Dataclasses - Phase 13.0
    BoneConfig,
    BoneConstraint,
    BoneGroupConfig,
    IKChain,
    RigConfig,
    WeightConfig,
    RigInstance,
    PoseData,
    # Dataclasses - Phase 13.1
    IKConfig,
    FKConfig,
    RotationLimits,
    PoleTargetConfig,
    IKFKBlendConfig,
    SplineIKConfig,
)

# Preset Loader
from .preset_loader import (
    load_rig_preset,
    list_available_presets,
    save_rig_config,
    clear_cache,
    get_preset_path,
    preset_exists,
    validate_preset,
)

# Rig Builder
from .rig_builder import (
    RigBuilder,
    build_rig_from_config,
    build_rig_from_preset,
    create_custom_rig,
    duplicate_rig,
    merge_rigs,
)

# Bone Utilities
from .bone_utils import (
    get_bone_chain,
    mirror_bone_name,
    get_bone_length,
    get_bone_direction,
    align_bone_to_vector,
    scale_bone,
    duplicate_bone_chain,
    connect_bone_chain,
    clear_bone_constraints,
    copy_bone_constraints,
    get_bone_world_matrix,
    get_bone_world_head,
    get_bone_world_tail,
    select_bone_chain,
    hide_bone_chain,
    get_all_bone_names,
    get_deform_bones,
    rename_bone_prefix,
)

# Weight Painter
from .weight_painter import (
    AutoWeightPainter,
    auto_weight_mesh,
    parent_mesh_to_armature,
    transfer_weights,
    mirror_weights,
    clean_weights,
    limit_influence,
)

# IK System - Phase 13.1
from .ik_system import (
    IKSystem,
    add_ik_to_bone,
    create_ik_setup,
)

# FK System - Phase 13.1
from .fk_system import (
    FKSystem,
    set_bone_rotation,
    get_bone_rotation,
    apply_rotation_limits_preset,
)

# IK/FK Blend - Phase 13.1
from .ik_fk_blend import (
    IKFKBlender,
    create_ikfk_setup,
    blend_to_ik,
    blend_to_fk,
    get_snap_rotation,
)

# Pole Targets - Phase 13.1
from .pole_targets import (
    PoleTargetManager,
    create_elbow_pole,
    create_knee_pole,
    auto_position_poles,
)

# Rotation Limits - Phase 13.1
from .rotation_limits import (
    RotationLimitEnforcer,
    apply_joint_limits,
    clamp_rotation,
)

# IK Presets - Phase 13.1
from .ik_presets import (
    list_ik_presets,
    ik_preset_exists,
    load_ik_preset,
    load_spline_ik_preset,
    load_blend_preset,
    save_ik_config,
    load_limb_ik_presets,
    load_chain_ik_presets,
)

# Pose Library - Phase 13.2
from .types import (
    PoseCategory,
    PoseMirrorAxis,
    PoseBlendMode,
    BonePose,
    Pose,
    PoseBlendConfig,
    PoseLibraryConfig,
)

from .pose_library import (
    PoseLibrary,
    capture_current_pose,
    apply_pose_by_id,
    save_pose_to_library,
    list_available_poses,
)

from .pose_blending import (
    PoseBlender,
    blend_two_poses,
    blend_multiple_poses,
    apply_pose_blend,
    create_pose_transition,
)

from .pose_utils import (
    PoseMirror,
    PoseUtils,
    mirror_current_pose,
    mirror_pose,
    get_mirror_bone_name,
    compare_poses,
    extract_bones_from_pose,
)

# Blocking System - Phase 13.3
from .types import (
    InterpolationMode,
    KeyPoseType,
    KeyPose,
    BlockingSession,
    OnionSkinConfig,
    TimelineMarkerConfig,
    BlockingPreset,
)

from .blocking import (
    BlockingSystem,
    start_blocking,
    create_blocking_session,
    add_key_pose_to_session,
    get_blocking_summary,
)

from .keyframe_markers import (
    KeyPoseMarkers,
    PoseThumbnails,
    TimelineNavigator,
    create_marker_for_key_pose,
    sync_markers_from_key_poses,
    get_navigation_frames,
)

from .onion_skin import (
    OnionSkinning,
    OnionSkinManager,
    enable_onion_skin,
    create_onion_skin_config,
    get_ghost_frame_list,
)

# Face Animation - Phase 13.4
from .types import (
    FaceRigComponent,
    ExpressionCategory,
    VisemeType,
    ShapeKeyCategory,
    ShapeKeyConfig,
    ExpressionConfig,
    FaceRigConfig,
    LipSyncFrame,
    LipSyncConfig,
    EyeTargetConfig,
    BlinkConfig,
)

from .face_rig import (
    FaceRigBuilder,
    FaceRigStats,
    create_face_rig,
    get_default_shape_keys,
    get_bilateral_pairs,
    get_face_rig_summary,
)

from .shape_keys import (
    ShapeKeySlider,
    ShapeKeyGroup,
    ShapeKeyManager,
    ShapeKeyCorrective,
    create_shape_key_manager,
    get_expression_shape_key_names,
    create_default_expression_shape_keys,
    calculate_combination_weight,
)

from .visemes import (
    VisemeMapper,
    LipSyncGenerator,
    LipSyncPlayer,
    PhonemeTiming,
    create_viseme_mapper,
    get_viseme_names,
    get_vowel_visemes,
    get_consonant_visemes,
    quick_lip_sync,
)

# Crowd System - Phase 13.5
from .types import (
    CrowdType,
    BehaviorState,
    DistributionType,
    AgentConfig,
    BehaviorConfig,
    SpawnConfig,
    AvoidanceConfig,
    VariationConfig,
    CrowdConfig,
    BoidRuleConfig,
    BoidSettingsConfig,
    MAX_PARTICLE_COUNT,
    WARN_PARTICLE_COUNT,
)

from .crowd import (
    # Boids Wrapper
    BoidsWrapper,
    create_flock,
    create_swarm,
    create_herd,
    # Plugin Interface
    CrowdPluginInterface,
    BoidsPlugin,
    BlenderCrowdPlugin,
    get_plugin,
    get_available_plugins,
    is_plugin_available,
    # Crowd Config
    CrowdConfigManager,
    load_crowd_config,
    save_crowd_config,
    list_crowd_configs,
    validate_crowd_config,
)

# Vehicle System - Phase 13.6
from .types import (
    VehicleType,
    SuspensionType,
    LaunchState,
    StuntType,
    WheelConfig,
    SteeringConfig,
    VehicleDimensions,
    VehicleConfig,
    LaunchConfig,
    DriverProfile,
    DRIVER_PRESETS,
)

# Vehicle imports require bpy - make conditional for testing
try:
    from .vehicle import (
        # Wheel System
        WheelSystem,
        setup_car_wheels,
        # Suspension
        SuspensionSystem,
        setup_vehicle_suspension,
        # Plugin Interface
        VehiclePluginInterface,
        BlenderPhysicsVehicle,
        # Vehicle Config
        VehicleConfigManager,
        load_vehicle_config,
        save_vehicle_config,
        list_vehicle_configs,
        validate_vehicle_config,
        create_default_vehicle_config,
        # Launch Control
        LaunchController,
        create_launch_controller,
        # Stunt Coordinator
        StuntCoordinator,
        create_stunt_coordinator,
        # Driver System
        ExpertDriver,
        get_driver_profile,
        DRIVER_PRESETS as VEHICLE_DRIVER_PRESETS,
    )
    _VEHICLE_AVAILABLE = True
except ImportError:
    _VEHICLE_AVAILABLE = False
    # Define placeholders for vehicle exports when bpy is not available
    WheelSystem = None
    setup_car_wheels = None
    SuspensionSystem = None
    setup_vehicle_suspension = None
    VehiclePluginInterface = None
    BlenderPhysicsVehicle = None
    VehicleConfigManager = None
    load_vehicle_config = None
    save_vehicle_config = None
    list_vehicle_configs = None
    validate_vehicle_config = None
    create_default_vehicle_config = None
    LaunchController = None
    create_launch_controller = None
    StuntCoordinator = None
    create_stunt_coordinator = None
    ExpertDriver = None
    get_driver_profile = None
    VEHICLE_DRIVER_PRESETS = {}

# Animation Layers - Phase 13.7
from .types import (
    LayerType,
    BoneKeyframe,
    LayerKeyframe,
    AnimationLayer,
    LayerStack,
    LayerPreset,
)

from .layers import (
    # Layer System
    AnimationLayerSystem,
    create_layer_system,
    get_layer_presets_directory,
    list_layer_presets,
    load_layer_preset,
    apply_layer_preset,
    # Layer Blending
    LayerBlender,
    blend_layers,
    blend_layer_range,
    # Layer Masking
    LayerMaskManager,
    apply_mask_to_layer,
    create_custom_mask,
    list_available_masks,
)


__all__ = [
    # Types - Enums
    'RigType',
    'BoneGroupType',
    'WeightMethod',
    'IKMode',
    'RotationOrder',
    'BlendMode',
    # Types - Dataclasses (Phase 13.0)
    'BoneConfig',
    'BoneConstraint',
    'BoneGroupConfig',
    'IKChain',
    'RigConfig',
    'WeightConfig',
    'RigInstance',
    'PoseData',
    # Types - Dataclasses (Phase 13.1)
    'IKConfig',
    'FKConfig',
    'RotationLimits',
    'PoleTargetConfig',
    'IKFKBlendConfig',
    'SplineIKConfig',

    # Preset Loader
    'load_rig_preset',
    'list_available_presets',
    'save_rig_config',
    'clear_cache',
    'get_preset_path',
    'preset_exists',
    'validate_preset',

    # Rig Builder
    'RigBuilder',
    'build_rig_from_config',
    'build_rig_from_preset',
    'create_custom_rig',
    'duplicate_rig',
    'merge_rigs',

    # Bone Utilities
    'get_bone_chain',
    'mirror_bone_name',
    'get_bone_length',
    'get_bone_direction',
    'align_bone_to_vector',
    'scale_bone',
    'duplicate_bone_chain',
    'connect_bone_chain',
    'clear_bone_constraints',
    'copy_bone_constraints',
    'get_bone_world_matrix',
    'get_bone_world_head',
    'get_bone_world_tail',
    'select_bone_chain',
    'hide_bone_chain',
    'get_all_bone_names',
    'get_deform_bones',
    'rename_bone_prefix',

    # Weight Painter
    'AutoWeightPainter',
    'auto_weight_mesh',
    'parent_mesh_to_armature',
    'transfer_weights',
    'mirror_weights',
    'clean_weights',
    'limit_influence',

    # IK System (Phase 13.1)
    'IKSystem',
    'add_ik_to_bone',
    'create_ik_setup',

    # FK System (Phase 13.1)
    'FKSystem',
    'set_bone_rotation',
    'get_bone_rotation',
    'apply_rotation_limits_preset',

    # IK/FK Blend (Phase 13.1)
    'IKFKBlender',
    'create_ikfk_setup',
    'blend_to_ik',
    'blend_to_fk',
    'get_snap_rotation',

    # Pole Targets (Phase 13.1)
    'PoleTargetManager',
    'create_elbow_pole',
    'create_knee_pole',
    'auto_position_poles',

    # Rotation Limits (Phase 13.1)
    'RotationLimitEnforcer',
    'apply_joint_limits',
    'clamp_rotation',

    # IK Presets (Phase 13.1)
    'list_ik_presets',
    'ik_preset_exists',
    'load_ik_preset',
    'load_spline_ik_preset',
    'load_blend_preset',
    'save_ik_config',
    'load_limb_ik_presets',
    'load_chain_ik_presets',

    # Types - Phase 13.2 (Pose Library)
    'PoseCategory',
    'PoseMirrorAxis',
    'PoseBlendMode',
    'BonePose',
    'Pose',
    'PoseBlendConfig',
    'PoseLibraryConfig',

    # Pose Library (Phase 13.2)
    'PoseLibrary',
    'capture_current_pose',
    'apply_pose_by_id',
    'save_pose_to_library',
    'list_available_poses',

    # Pose Blending (Phase 13.2)
    'PoseBlender',
    'blend_two_poses',
    'blend_multiple_poses',
    'apply_pose_blend',
    'create_pose_transition',

    # Pose Utils (Phase 13.2)
    'PoseMirror',
    'PoseUtils',
    'mirror_current_pose',
    'mirror_pose',
    'get_mirror_bone_name',
    'compare_poses',
    'extract_bones_from_pose',

    # Types - Phase 13.3 (Blocking System)
    'InterpolationMode',
    'KeyPoseType',
    'KeyPose',
    'BlockingSession',
    'OnionSkinConfig',
    'TimelineMarkerConfig',
    'BlockingPreset',

    # Blocking System (Phase 13.3)
    'BlockingSystem',
    'start_blocking',
    'create_blocking_session',
    'add_key_pose_to_session',
    'get_blocking_summary',

    # Keyframe Markers (Phase 13.3)
    'KeyPoseMarkers',
    'PoseThumbnails',
    'TimelineNavigator',
    'create_marker_for_key_pose',
    'sync_markers_from_key_poses',
    'get_navigation_frames',

    # Onion Skinning (Phase 13.3)
    'OnionSkinning',
    'OnionSkinManager',
    'enable_onion_skin',
    'create_onion_skin_config',
    'get_ghost_frame_list',

    # Types - Phase 13.4 (Face Animation)
    'FaceRigComponent',
    'ExpressionCategory',
    'VisemeType',
    'ShapeKeyCategory',
    'ShapeKeyConfig',
    'ExpressionConfig',
    'FaceRigConfig',
    'LipSyncFrame',
    'LipSyncConfig',
    'EyeTargetConfig',
    'BlinkConfig',

    # Face Rig (Phase 13.4)
    'FaceRigBuilder',
    'FaceRigStats',
    'create_face_rig',
    'get_default_shape_keys',
    'get_bilateral_pairs',
    'get_face_rig_summary',

    # Shape Keys (Phase 13.4)
    'ShapeKeySlider',
    'ShapeKeyGroup',
    'ShapeKeyManager',
    'ShapeKeyCorrective',
    'create_shape_key_manager',
    'get_expression_shape_key_names',
    'create_default_expression_shape_keys',
    'calculate_combination_weight',

    # Visemes (Phase 13.4)
    'VisemeMapper',
    'LipSyncGenerator',
    'LipSyncPlayer',
    'PhonemeTiming',
    'create_viseme_mapper',
    'get_viseme_names',
    'get_vowel_visemes',
    'get_consonant_visemes',
    'quick_lip_sync',

    # Types - Phase 13.5 (Crowd System)
    'CrowdType',
    'BehaviorState',
    'DistributionType',
    'AgentConfig',
    'BehaviorConfig',
    'SpawnConfig',
    'AvoidanceConfig',
    'VariationConfig',
    'CrowdConfig',
    'BoidRuleConfig',
    'BoidSettingsConfig',
    'MAX_PARTICLE_COUNT',
    'WARN_PARTICLE_COUNT',

    # Crowd System - Phase 13.5
    'BoidsWrapper',
    'create_flock',
    'create_swarm',
    'create_herd',
    'CrowdPluginInterface',
    'BoidsPlugin',
    'BlenderCrowdPlugin',
    'get_plugin',
    'get_available_plugins',
    'is_plugin_available',
    'CrowdConfigManager',
    'load_crowd_config',
    'save_crowd_config',
    'list_crowd_configs',
    'validate_crowd_config',

    # Types - Phase 13.6 (Vehicle System)
    'VehicleType',
    'SuspensionType',
    'LaunchState',
    'StuntType',
    'WheelConfig',
    'SteeringConfig',
    'VehicleDimensions',
    'VehicleConfig',
    'LaunchConfig',
    'DriverProfile',
    'DRIVER_PRESETS',

    # Vehicle System - Phase 13.6
    'WheelSystem',
    'setup_car_wheels',
    'SuspensionSystem',
    'setup_vehicle_suspension',
    'VehiclePluginInterface',
    'BlenderPhysicsVehicle',
    'VehicleConfigManager',
    'load_vehicle_config',
    'save_vehicle_config',
    'list_vehicle_configs',
    'validate_vehicle_config',
    'create_default_vehicle_config',
    'LaunchController',
    'create_launch_controller',
    'StuntCoordinator',
    'create_stunt_coordinator',
    'ExpertDriver',
    'get_driver_profile',

    # Types - Phase 13.7 (Animation Layers)
    'LayerType',
    'BoneKeyframe',
    'LayerKeyframe',
    'AnimationLayer',
    'LayerStack',
    'LayerPreset',

    # Animation Layers - Phase 13.7
    'AnimationLayerSystem',
    'create_layer_system',
    'get_layer_presets_directory',
    'list_layer_presets',
    'load_layer_preset',
    'apply_layer_preset',
    'LayerBlender',
    'blend_layers',
    'blend_layer_range',
    'LayerMaskManager',
    'apply_mask_to_layer',
    'create_custom_mask',
    'list_available_masks',
]


__version__ = "0.7.0"
