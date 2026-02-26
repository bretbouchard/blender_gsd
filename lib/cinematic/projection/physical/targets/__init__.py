"""
Target presets for physical projector mapping.

Provides types and builders for creating projection targets (surfaces)
from preset configurations or custom definitions.

Usage:
    from lib.cinematic.projection.physical.targets import (
        TargetType,
        ProjectionTarget,
        ProjectionSurface,
        PlanarTargetBuilder,
        create_builder,
        TargetImporter,
        preview_target,
    )

    # Create a target from scratch
    target = ProjectionTarget(
        name="my_target",
        description="Custom projection surface",
        target_type=TargetType.PLANAR,
        width_m=3.0,
        height_m=2.0,
    )

    # Build geometry
    builder = create_builder(target)
    result = builder.create_geometry()

    # Or import from measurements
    importer = TargetImporter()
    importer.add_point_measurement("corner", (0, 0, 0))
    target = importer.compute_target()

    # Preview in viewport
    preview = preview_target(target)
"""

# Types
from .types import (
    TargetType,
    SurfaceMaterial,
    ProjectionSurface,
    ProjectionTarget,
    TargetGeometryResult,
    PLANAR_2X2M,
    GARAGE_DOOR_STANDARD,
)

# Builders
from .base import (
    TargetBuilder,
    PlanarTargetBuilder,
    MultiSurfaceTargetBuilder,
    create_builder,
)

# Import system
from .import_system import (
    MeasurementInput,
    MeasurementSet,
    TargetImporter,
)

# Preview system
from .preview import (
    PreviewConfig,
    PreviewResult,
    TargetPreview,
    preview_target,
)

# Presets
from .presets import (
    load_target_preset,
    list_target_presets,
    create_reading_room_target,
    create_garage_door_target,
    create_building_facade_target,
)

__all__ = [
    # Types
    'TargetType',
    'SurfaceMaterial',
    'ProjectionSurface',
    'ProjectionTarget',
    'TargetGeometryResult',

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
    'PLANAR_2X2M',
    'GARAGE_DOOR_STANDARD',
]

__version__ = '0.2.0'
