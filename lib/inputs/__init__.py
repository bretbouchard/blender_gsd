"""
Universal Input System

A comprehensive system for generating procedural input controls:
- Rotary inputs (knobs)
- Linear inputs (faders, sliders)
- Momentary inputs (buttons)

All inputs use a zone-based geometry system with reusable
Geometry Node groups stored in assets/inputs.blend.

Usage:
    from lib.inputs import build_input, get_preset, list_presets

    # Build from preset
    build_input(preset="knob_neve_1073", collection=my_collection)

    # Build with overrides
    build_input(
        preset="knob_neve_1073",
        overrides={"zones.a.width_top_mm": 16},
        collection=my_collection
    )

    # List available presets
    presets = list_presets(input_type="rotary")
"""

from .input_types import (
    # Enums
    InputType,
    BaseShape,
    CapStyle,
    KnurlProfile,
    RotationMode,
    # Config classes
    CapConfig,
    KnurlConfig,
    ZoneConfig,
    RotationConfig,
    InputConfig,
)

from .zone_geometry import (
    ZoneGeometry,
    ZoneBuilder,
)

from .input_presets import (
    InputPreset,
    PresetManager,
    get_preset,
    list_presets,
    create_preset,
)

from .builder import (
    build_input,
    build_from_config,
)

from .debug_materials import (
    DEBUG_COLORS,
    DEBUG_PRESETS,
    SECTION_NAMES,
    create_debug_material,
    create_debug_palette,
    create_all_debug_materials,
    get_debug_color,
)

__all__ = [
    # Enums
    "InputType",
    "BaseShape",
    "CapStyle",
    "KnurlProfile",
    "RotationMode",

    # Config classes
    "CapConfig",
    "KnurlConfig",
    "ZoneConfig",
    "RotationConfig",
    "InputConfig",

    # Geometry
    "ZoneGeometry",
    "ZoneBuilder",

    # Presets
    "InputPreset",
    "PresetManager",
    "get_preset",
    "list_presets",
    "create_preset",

    # Builder
    "build_input",
    "build_from_config",

    # Debug materials
    "DEBUG_COLORS",
    "DEBUG_PRESETS",
    "SECTION_NAMES",
    "create_debug_material",
    "create_debug_palette",
    "create_all_debug_materials",
    "get_debug_color",
]

__version__ = "0.1.0"
