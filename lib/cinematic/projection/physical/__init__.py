"""
Physical projector mapping system.

This package provides tools for mapping content to physical projectors
in real-world environments.

Components:
- projector: Hardware profiles and calibration utilities
- calibration: Surface calibration and alignment (Phase 18.1)
- stages: Pipeline stage functions (Phase 18.0)
- targets: Projection surface configurations (Phase 18.3)
- shaders: Camera projection shader nodes (Phase 18.2)
- output: Projection output rendering (Phase 18.2)
- workflow: Content mapping workflow integration (Phase 18.2)
- integration: Shot YAML integration (Phase 18.4)

Workflow:
1. Select projector profile from database
2. Create Blender camera from profile
3. Calibrate to real-world surface (Phase 18.1)
4. Map content to surface (Phase 18.2)
5. Render at projector native resolution (Phase 18.2)

Example:
    from lib.cinematic.projection.physical import (
        load_profile,
        create_projector_camera,
        ContentMappingWorkflow,
        render_for_projector,
    )

    # Simple one-shot rendering
    files = render_for_projector(
        content_path="//content/animation.mp4",
        projector_profile_name="Epson_Home_Cinema_2150",
        calibration_points=[
            ((0, 0, 0), (0, 0)),  # Bottom-left
            ((2, 0, 0), (1, 0)),  # Bottom-right
            ((0, 1.5, 0), (0, 1)), # Top-left
        ],
        output_dir="//projector_output/"
    )

    # Or use the full workflow
    profile = load_profile("Epson_Home_Cinema_2150")
    workflow = ContentMappingWorkflow(
        name="my_projection",
        projector_profile=profile,
        calibration=calibration
    )
    workflow.execute(content_path, output_dir)

    # Or build from YAML
    from lib.cinematic.projection.physical.integration import build_projection_shot
    result = build_projection_shot("shots/my_projection.yaml")
"""

# Projector profiles (Phase 18.0)
from .projector import (
    # Types
    ProjectorProfile,
    ProjectorType,
    AspectRatio,
    LensShift,
    KeystoneCorrection,
    # Database
    PROJECTOR_PROFILES,
    get_profile,
    list_profiles,
    get_profiles_by_throw_ratio,
    get_profiles_by_resolution,
    get_short_throw_profiles,
    get_4k_profiles,
    load_profile,
    load_profile_from_yaml,
    # Calibration utilities
    throw_ratio_to_focal_length,
    focal_length_to_throw_ratio,
    calculate_throw_distance,
    calculate_image_width,
    create_projector_camera,
    configure_render_for_projector,
    restore_render_settings,
)

# Calibration (Phase 18.1)
from .calibration import (
    # Types
    CalibrationPoint,
    CalibrationType,
    SurfaceCalibration,
    CalibrationPattern,
    PatternType,
    AlignmentResult,
    # Alignment
    compute_alignment_transform,
    build_orthonormal_basis,
    are_collinear,
    # DLT
    four_point_dlt_alignment,
    decompose_projection_matrix,
    # Patterns
    generate_checkerboard_pattern,
    generate_color_bars_pattern,
    generate_grid_pattern,
    # Keystone
    compute_keystone_correction,
    apply_keystone_to_camera,
    # Manager
    CalibrationManager,
)
# Import Vector3 from alignment
from .calibration.alignment import Vector3

# Shaders (Phase 18.2)
from .shaders import (
    # Types
    ProjectionMode,
    BlendMode,
    TextureFilter,
    TextureExtension,
    ProjectionShaderConfig,
    ProjectionShaderResult,
    ProxyGeometryConfig,
    ProxyGeometryResult,
    # Shader creation
    create_projector_material,
    ensure_projector_projection_group,
    update_projection_content,
    set_projection_intensity,
    # Proxy geometry
    create_proxy_geometry_for_surface,
    create_planar_proxy_vertices,
    compute_uv_for_calibration_points,
    subdivide_quad,
    subdivide_uv,
    create_proxy_mesh_blender,
    create_multi_surface_proxy,
    # Content mapping
    ContentMapper,
    ContentMappingResult,
    map_content_to_projector,
)

# Output (Phase 18.2)
from .output import (
    # Types
    OutputFormat,
    ColorSpace,
    VideoCodec,
    EXRCodec,
    ProjectionOutputConfig,
    ProjectionOutputResult,
    CalibrationPatternConfig,
    # Renderer
    ProjectionOutputRenderer,
    # Multi-surface
    MultiSurfaceOutput,
    MultiSurfaceResult,
    MultiSurfaceRenderer,
)

# Workflow (Phase 18.2)
from .workflow import (
    ContentMappingWorkflow,
    render_for_projector,
    create_multi_surface_workflow,
)

# Stage pipeline (Phase 18.0)
from .stages import (
    StageContext,
    StageState,
    stage_normalize,
    stage_primary,
)

# Targets (Phase 18.3)
from .targets import (
    # Types
    TargetType,
    SurfaceMaterial,
    ProjectionSurface,
    ProjectionTarget,
    TargetGeometryResult,
    PLANAR_2X2M,
    GARAGE_DOOR_STANDARD,
    # Builders
    TargetBuilder,
    PlanarTargetBuilder,
    MultiSurfaceTargetBuilder,
    create_builder,
    # Import
    MeasurementInput,
    MeasurementSet,
    TargetImporter,
    # Preview
    PreviewConfig,
    PreviewResult,
    TargetPreview,
    preview_target,
    # Presets
    load_target_preset,
    list_target_presets,
    create_reading_room_target,
    create_garage_door_target,
    create_building_facade_target,
)

# Integration (Phase 18.4)
from .integration import (
    ProjectionShotConfig,
    ProjectionShotResult,
    ProjectionShotBuilder,
    build_projection_shot,
    build_projection_shot_from_dict,
)


__all__ = [
    # === Projector Profiles (Phase 18.0) ===
    # Types
    'ProjectorProfile',
    'ProjectorType',
    'AspectRatio',
    'LensShift',
    'KeystoneCorrection',
    # Database
    'PROJECTOR_PROFILES',
    'get_profile',
    'list_profiles',
    'get_profiles_by_throw_ratio',
    'get_profiles_by_resolution',
    'get_short_throw_profiles',
    'get_4k_profiles',
    'load_profile',
    'load_profile_from_yaml',
    # Calibration utilities
    'throw_ratio_to_focal_length',
    'focal_length_to_throw_ratio',
    'calculate_throw_distance',
    'calculate_image_width',
    'create_projector_camera',
    'configure_render_for_projector',
    'restore_render_settings',

    # === Calibration (Phase 18.1) ===
    # Types
    'CalibrationPoint',
    'CalibrationType',
    'SurfaceCalibration',
    'CalibrationPattern',
    'PatternType',
    'AlignmentResult',
    'Vector3',
    # Alignment
    'compute_alignment_transform',
    'build_orthonormal_basis',
    'are_collinear',
    # DLT
    'four_point_dlt_alignment',
    'decompose_projection_matrix',
    # Patterns
    'generate_checkerboard_pattern',
    'generate_color_bars_pattern',
    'generate_grid_pattern',
    # Keystone
    'compute_keystone_correction',
    'apply_keystone_to_camera',
    # Manager
    'CalibrationManager',

    # === Shaders (Phase 18.2) ===
    # Types
    'ProjectionMode',
    'BlendMode',
    'TextureFilter',
    'TextureExtension',
    'ProjectionShaderConfig',
    'ProjectionShaderResult',
    'ProxyGeometryConfig',
    'ProxyGeometryResult',
    # Shader creation
    'create_projector_material',
    'ensure_projector_projection_group',
    'update_projection_content',
    'set_projection_intensity',
    # Proxy geometry
    'create_proxy_geometry_for_surface',
    'create_planar_proxy_vertices',
    'compute_uv_for_calibration_points',
    'subdivide_quad',
    'subdivide_uv',
    'create_proxy_mesh_blender',
    'create_multi_surface_proxy',
    # Content mapping
    'ContentMapper',
    'ContentMappingResult',
    'map_content_to_projector',

    # === Output (Phase 18.2) ===
    # Types
    'OutputFormat',
    'ColorSpace',
    'VideoCodec',
    'EXRCodec',
    'ProjectionOutputConfig',
    'ProjectionOutputResult',
    'CalibrationPatternConfig',
    # Renderer
    'ProjectionOutputRenderer',
    # Multi-surface
    'MultiSurfaceOutput',
    'MultiSurfaceResult',
    'MultiSurfaceRenderer',

    # === Workflow (Phase 18.2) ===
    'ContentMappingWorkflow',
    'render_for_projector',
    'create_multi_surface_workflow',

    # === Stages (Phase 18.0) ===
    'StageContext',
    'StageState',
    'stage_normalize',
    'stage_primary',

    # === Targets (Phase 18.3) ===
    # Types
    'TargetType',
    'SurfaceMaterial',
    'ProjectionSurface',
    'ProjectionTarget',
    'TargetGeometryResult',
    'PLANAR_2X2M',
    'GARAGE_DOOR_STANDARD',
    # Builders
    'TargetBuilder',
    'PlanarTargetBuilder',
    'MultiSurfaceTargetBuilder',
    'create_builder',
    # Import
    'MeasurementInput',
    'MeasurementSet',
    'TargetImporter',
    # Preview
    'PreviewConfig',
    'PreviewResult',
    'TargetPreview',
    'preview_target',
    # Presets
    'load_target_preset',
    'list_target_presets',
    'create_reading_room_target',
    'create_garage_door_target',
    'create_building_facade_target',

    # === Integration (Phase 18.4) ===
    'ProjectionShotConfig',
    'ProjectionShotResult',
    'ProjectionShotBuilder',
    'build_projection_shot',
    'build_projection_shot_from_dict',
]

__version__ = '0.3.0'
