"""
Integration module for physical projection system.

Provides tools for integrating the projection system with shot YAML
configuration and cinematic pipelines.

Usage:
    from lib.cinematic.projection.physical.integration import (
        ProjectionShotConfig,
        ProjectionShotBuilder,
        build_projection_shot,
    )

    # Build from YAML file
    result = build_projection_shot("shots/my_projection.yaml")

    # Or build programmatically
    config = ProjectionShotConfig(
        name="My Shot",
        projector_profile="epson_home_cinema_2150",
        calibration_points=[...],
    )
    builder = ProjectionShotBuilder(config)
    result = builder.build()
"""

from .shot import (
    ProjectionShotConfig,
    ProjectionShotResult,
    ProjectionShotBuilder,
    build_projection_shot,
    build_projection_shot_from_dict,
)

__all__ = [
    'ProjectionShotConfig',
    'ProjectionShotResult',
    'ProjectionShotBuilder',
    'build_projection_shot',
    'build_projection_shot_from_dict',
]

__version__ = '0.1.0'
