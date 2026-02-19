"""
Cinematic Projection Module

Anamorphic / forced perspective projection system for creating
images that only appear correct from specific camera viewpoints.

Part of Phase 9.0 - Projection Foundation (REQ-ANAM-01)
Part of Phase 9.1 - Surface Detection (REQ-ANAM-02)
Part of Phase 9.2 - UV Generation (REQ-ANAM-03)
Part of Phase 9.3 - Texture Baking (REQ-ANAM-04)
Part of Phase 9.4 - Camera Position Zones (REQ-ANAM-05)
Beads: blender_gsd-34, blender_gsd-35, blender_gsd-36, blender_gsd-37, blender_gsd-38

Usage:
    from lib.cinematic.projection import (
        # Types
        RayHit,
        FrustumConfig,
        ProjectionResult,
        AnamorphicProjectionConfig,
        SurfaceInfo,
        SurfaceType,
        ProjectionMode,
        OcclusionResult,
        MultiSurfaceGroup,
        SurfaceSelectionMask,

        # Raycasting
        generate_frustum_rays,
        cast_ray,
        project_from_camera,
        detect_surfaces_in_frustum,
        get_pixel_ray,

        # Surface Detection
        detect_surfaces,
        detect_occlusion,
        detect_multi_surface_groups,
        create_surface_selection_mask,
        filter_surfaces_by_type,
        get_best_projection_surfaces,

        # UV Generation
        UVGenerationResult,
        UVSeamInfo,
        UVLayoutConfig,
        generate_uvs_from_projection,
        generate_uvs_for_surface,
        detect_uv_seams,
        apply_uv_seams,
        optimize_uv_layout,
        validate_uv_layout,

        # Texture Baking
        BakeConfig,
        BakeResult,
        BakeMode,
        BakeFormat,
        bake_projection_texture,
        bake_object_texture,
        create_bake_material,
        prepare_for_baking,
        cleanup_bake_artifacts,
        export_baked_textures,

        # Camera Zones
        ZoneType,
        ZoneTransition,
        CameraZone,
        ZoneState,
        ZoneManager,
        ZoneManagerConfig,
        create_sphere_zone,
        create_box_zone,
        create_sweet_spot,
        get_zone_visualization_data,

        # Utilities
        classify_surface_type,
        is_surface_in_frustum,
        calculate_projection_scale,
        get_projection_bounds,
        create_frustum_visualization,
        estimate_projection_quality,
    )

    # Create projection config
    config = FrustumConfig(
        resolution_x=1920,
        resolution_y=1080,
        fov=50.0,
    )

    # Project from camera
    result = project_from_camera("Camera", config, "source_image.png")

    # Access hits
    for obj_name, hits in result.hits_by_object.items():
        print(f"{obj_name}: {len(hits)} ray hits")

    # Generate UVs from projection
    uv_results = generate_uvs_from_projection(result)
    for uv_result in uv_results:
        print(f"{uv_result.object_name}: {uv_result.coverage:.1f}% coverage")

    # Bake texture
    proj_config = AnamorphicProjectionConfig(
        source_image="artwork.png",
        camera_name="Camera",
        projection_mode=ProjectionMode.EMISSION,
    )
    bake_results = bake_projection_texture(proj_config)

    # Create sweet spot zone
    zone = create_sweet_spot(
        installation_name="floor_art",
        camera_position=(0, 5, 1.6),
        sweet_spot_radius=0.5,
        target_objects=["FloorArt"],
    )

    # Manage zones
    manager = ZoneManager()
    manager.add_zone(zone)
    state = manager.evaluate((0, 5, 1.6))

    # Detect surfaces with occlusion checking
    surfaces = detect_surfaces("Camera", config, check_occlusion=True)

    # Find floor surfaces
    floors = filter_surfaces_by_type(surfaces, [SurfaceType.FLOOR])

    # Get best projection surfaces
    best = get_best_projection_surfaces(surfaces, "Camera", prefer_type=SurfaceType.FLOOR)

    # Check coverage
    quality = estimate_projection_quality(result.hits, surface_area=10.0)
    print(f"Projection quality: {quality['quality']}")
"""

from .types import (
    # Enums
    SurfaceType,
    ProjectionMode,

    # Data classes
    RayHit,
    FrustumConfig,
    ProjectionResult,
    AnamorphicProjectionConfig,
    SurfaceInfo,
)

from .raycast import (
    # Core functions
    generate_frustum_rays,
    cast_ray,
    project_from_camera,
    detect_surfaces_in_frustum,
    get_pixel_ray,
)

from .surface_detection import (
    # Data classes
    OcclusionResult,
    MultiSurfaceGroup,
    SurfaceSelectionMask,

    # Surface detection functions
    detect_surfaces,
    detect_occlusion,
    detect_multi_surface_groups,
    create_surface_selection_mask,
    filter_surfaces_by_type,
    get_best_projection_surfaces,
)

from .uv_generation import (
    # Data classes
    UVGenerationResult,
    UVSeamInfo,
    UVLayoutConfig,

    # UV generation functions
    generate_uvs_from_projection,
    generate_uvs_for_surface,
    detect_uv_seams,
    apply_uv_seams,
    optimize_uv_layout,
    validate_uv_layout,
)

from .baking import (
    # Classes
    BakeMode,
    BakeFormat,

    # Data classes
    BakeConfig,
    BakeResult,

    # Baking functions
    bake_projection_texture,
    bake_object_texture,
    create_bake_material,
    prepare_for_baking,
    cleanup_bake_artifacts,
    export_baked_textures,
)

from .zones import (
    # Enums
    ZoneType,
    ZoneTransition,

    # Data classes
    CameraZone,
    ZoneState,
    ZoneManagerConfig,

    # Zone manager
    ZoneManager,

    # Zone functions
    create_sphere_zone,
    create_box_zone,
    create_sweet_spot,
    get_zone_visualization_data,
)

from .visibility import (
    # Constants
    VisibilityTransition,

    # Data classes
    VisibilityTarget,
    VisibilityState,
    VisibilityConfig,

    # Controller
    VisibilityController,

    # Functions
    create_visibility_target,
    setup_visibility_for_projection,
    evaluate_visibility_for_frame,
    bake_visibility_animation,
)

from .utils import (
    # Utility functions
    classify_surface_type,
    is_surface_in_frustum,
    calculate_projection_scale,
    get_projection_bounds,
    create_frustum_visualization,
    estimate_projection_quality,
)

__all__ = [
    # Enums
    "SurfaceType",
    "ProjectionMode",
    "ZoneType",
    "ZoneTransition",
    "VisibilityTransition",

    # Data classes
    "RayHit",
    "FrustumConfig",
    "ProjectionResult",
    "AnamorphicProjectionConfig",
    "SurfaceInfo",
    "OcclusionResult",
    "MultiSurfaceGroup",
    "SurfaceSelectionMask",
    "UVGenerationResult",
    "UVSeamInfo",
    "UVLayoutConfig",
    "BakeConfig",
    "BakeResult",
    "BakeMode",
    "BakeFormat",
    "CameraZone",
    "ZoneState",
    "ZoneManagerConfig",
    "VisibilityTarget",
    "VisibilityState",
    "VisibilityConfig",

    # Zone Manager
    "ZoneManager",

    # Visibility Controller
    "VisibilityController",

    # Raycasting
    "generate_frustum_rays",
    "cast_ray",
    "project_from_camera",
    "detect_surfaces_in_frustum",
    "get_pixel_ray",

    # Surface Detection
    "detect_surfaces",
    "detect_occlusion",
    "detect_multi_surface_groups",
    "create_surface_selection_mask",
    "filter_surfaces_by_type",
    "get_best_projection_surfaces",

    # UV Generation
    "generate_uvs_from_projection",
    "generate_uvs_for_surface",
    "detect_uv_seams",
    "apply_uv_seams",
    "optimize_uv_layout",
    "validate_uv_layout",

    # Texture Baking
    "bake_projection_texture",
    "bake_object_texture",
    "create_bake_material",
    "prepare_for_baking",
    "cleanup_bake_artifacts",
    "export_baked_textures",

    # Camera Zones
    "create_sphere_zone",
    "create_box_zone",
    "create_sweet_spot",
    "get_zone_visualization_data",

    # Visibility
    "create_visibility_target",
    "setup_visibility_for_projection",
    "evaluate_visibility_for_frame",
    "bake_visibility_animation",

    # Utilities
    "classify_surface_type",
    "is_surface_in_frustum",
    "calculate_projection_scale",
    "get_projection_bounds",
    "create_frustum_visualization",
    "estimate_projection_quality",
]

__version__ = "0.6.0"
