"""
Projection shader system for physical projector mapping.

This module provides:
- Projection shader types and configuration
- Camera projection node groups
- Proxy geometry generation
- Content mapping workflow

Usage:
    from lib.cinematic.projection.physical.shaders import (
        ContentMapper,
        ProjectionShaderConfig,
        create_projector_material,
    )

    # Create shader config
    config = ProjectionShaderConfig(
        throw_ratio=1.5,
        resolution_x=1920,
        resolution_y=1080,
    )

    # Create projection material
    result = create_projector_material(config, projector_camera)

    # Or use the high-level ContentMapper
    mapper = ContentMapper(projector_profile)
    result = mapper.map_content_to_surface(
        content_path="content.png",
        surface_object=surface,
        projector_object=projector,
        calibration=calibration
    )
"""

# Types
from .types import (
    # Enums
    ProjectionMode,
    BlendMode,
    TextureFilter,
    TextureExtension,
    # Configs
    ProjectionShaderConfig,
    ProjectionShaderResult,
    ProxyGeometryConfig,
    ProxyGeometryResult,
)

# Node functions
from .projector_nodes import (
    ensure_projector_projection_group,
    create_projector_material,
    update_projection_content,
    set_projection_intensity,
)

# Geometry functions
from .proxy_geometry import (
    create_planar_proxy_vertices,
    compute_uv_for_calibration_points,
    subdivide_quad,
    subdivide_uv,
    create_proxy_geometry_for_surface,
    create_proxy_mesh_blender,
    create_multi_surface_proxy,
)

# Content mapping
from .content_mapper import (
    ContentMapper,
    ContentMappingResult,
    map_content_to_projector,
)


__all__ = [
    # Enums
    "ProjectionMode",
    "BlendMode",
    "TextureFilter",
    "TextureExtension",
    # Configs
    "ProjectionShaderConfig",
    "ProjectionShaderResult",
    "ProxyGeometryConfig",
    "ProxyGeometryResult",
    # Node functions
    "ensure_projector_projection_group",
    "create_projector_material",
    "update_projection_content",
    "set_projection_intensity",
    # Geometry functions
    "create_planar_proxy_vertices",
    "compute_uv_for_calibration_points",
    "subdivide_quad",
    "subdivide_uv",
    "create_proxy_geometry_for_surface",
    "create_proxy_mesh_blender",
    "create_multi_surface_proxy",
    # Content mapping
    "ContentMapper",
    "ContentMappingResult",
    "map_content_to_projector",
]

__version__ = "0.1.0"
