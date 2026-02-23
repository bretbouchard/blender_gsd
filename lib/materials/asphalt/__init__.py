"""
Asphalt PBR Material System

Procedural and image-based asphalt materials for realistic road surfaces.

Features:
- Procedural asphalt with aggregate texture
- Multiple wear states (fresh, worn, damaged)
- Wet and dry variations
- Crack and pothole displacement
- Lane marking integration
- Performance-optimized node groups

Usage:
    from lib.materials.asphalt import (
        AsphaltMaterialBuilder,
        create_asphalt_material,
        create_highway_asphalt,
        AsphaltPreset,
    )

    # Create highway asphalt material
    builder = AsphaltMaterialBuilder()
    mat = builder.create("highway_asphalt", preset=AsphaltPreset.HIGHWAY)

    # Apply to road mesh
    builder.apply_to_object(road_mesh, mat)
"""

from .asphalt_pbr import (
    # Enums
    AsphaltType,
    AsphaltCondition,
    AsphaltPreset,
    # Dataclasses
    AsphaltConfig,
    AsphaltMaterialResult,
    # Builder
    AsphaltMaterialBuilder,
    # Convenience functions
    create_asphalt_material,
    create_highway_asphalt,
    create_residential_asphalt,
    create_worn_asphalt,
    create_wet_asphalt,
    # Presets
    ASPHALT_PRESETS,
)

__version__ = "1.0.0"
__all__ = [
    # Enums
    "AsphaltType",
    "AsphaltCondition",
    "AsphaltPreset",
    # Dataclasses
    "AsphaltConfig",
    "AsphaltMaterialResult",
    # Builder
    "AsphaltMaterialBuilder",
    # Functions
    "create_asphalt_material",
    "create_highway_asphalt",
    "create_residential_asphalt",
    "create_worn_asphalt",
    "create_wet_asphalt",
    # Presets
    "ASPHALT_PRESETS",
]
