"""
Mecha/Robot Parts Library

Manages mechanical parts for robot and vehicle assembly.
Supports Vitaly Bulgarov assets, custom parts, and kit integration.

Implements REQ-CH-04: Mecha/Robot Parts Library.
Implements REQ-CH-06: Assembly System.

Features:
- Parts catalog with categorization
- Assembly system for combining parts
- Scale normalization for mixed sources
- Material preset system
- Export to GN-compatible format

Asset Sources:
- Vitaly Bulgarov: ULTRABORG, Black Widow, Black Phoenix, etc.
- KitBash3D: Sci-Fi, vehicles, environments
- Custom designs: Personal library integration

Usage:
    from lib.mecha import PartsLibrary, Assembly

    # Load parts library
    library = PartsLibrary()
    library.index_directory("/Volumes/Storage/3d/animation/vitaly_bulgarov/")

    # Search for parts
    parts = library.search(category="armor", style="cyber")

    # Create assembly
    assembly = Assembly("my_robot")
    assembly.add_part("torso_ultraborg_01", position=(0, 0, 0))
    assembly.add_part("armor_plate_05", parent="torso", offset=(0, 0.1, 0))
    assembly.export_blend("robot.blend")

Compatibility:
    - Blender 4.x
    - Blender 5.x
"""

from __future__ import annotations

__all__ = [
    # Enums
    "PartCategory",
    "PartStyle",
    "PartSource",
    "AttachmentType",
    "AssemblyType",
    # Data classes
    "PartSpec",
    "AttachmentPoint",
    "PartVariant",
    "AssemblySpec",
    "AssemblyNode",
    # Constants
    "VITALY_BULGAROV_PACKS",
    "PART_SCALE_REFERENCE",
    "ATTACHMENT_PRESETS",
    # Classes
    "PartsLibrary",
    "Assembly",
    "AssemblyBuilder",
    # Functions
    "create_assembly",
    "load_parts_from_blend",
]

__version__ = "1.0.0"
__author__ = "Blender GSD Project"


from .parts_library import (
    # Enums
    PartCategory,
    PartStyle,
    PartSource,
    AttachmentType,
    # Data classes
    PartSpec,
    AttachmentPoint,
    PartVariant,
    # Constants
    VITALY_BULGAROV_PACKS,
    PART_SCALE_REFERENCE,
    # Classes
    PartsLibrary,
    # Functions
    load_parts_from_blend,
)

from .assembly import (
    # Enums
    AssemblyType,
    # Data classes
    AssemblySpec,
    AssemblyNode,
    # Constants
    ATTACHMENT_PRESETS,
    # Classes
    Assembly,
    AssemblyBuilder,
    # Functions
    create_assembly,
)
