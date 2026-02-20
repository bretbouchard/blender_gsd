"""
Art Module - Procedural Set Construction

Provides tools for building film/video sets procedurally including:
- Room generation with walls, floor, ceiling
- Door and window placement
- Prop population and dressing styles
- Style presets for various periods and aesthetics

Implements REQ-SET-01 through REQ-SET-05.
"""

from .set_types import (
    # Enums
    WallOrientation,
    DoorStyle,
    WindowStyle,
    SwingDirection,
    SetStyle,
    Period,
    PropCategory,
    DressingStyle,
    # Dataclasses
    WallConfig,
    DoorConfig,
    DoorPlacement,
    WindowConfig,
    WindowPlacement,
    RoomConfig,
    PropConfig,
    PropPlacement,
    SetConfig,
    StylePreset,
    # Constants
    DRESSING_STYLES,
    # Validation
    validate_wall_config,
    validate_door_config,
    validate_window_config,
    validate_room_config,
)

from .room_builder import (
    RoomMeshes,
    create_room,
    create_floor,
    create_ceiling,
    create_wall,
    add_wall_opening,
    create_molding,
    create_wainscoting,
    get_wall_bounds,
)

from .openings import (
    DoorMeshes,
    WindowMeshes,
    create_door,
    create_panel_door,
    create_flush_door,
    create_barn_door,
    create_french_door,
    create_glass_door,
    create_door_frame,
    create_door_handle,
    create_window,
    create_double_hung_window,
    create_casement_window,
    create_picture_window,
    create_slider_window,
    create_window_frame,
    create_window_sill,
    create_curtains,
    create_blinds,
    place_door,
    place_window,
)

from .props import (
    DEFAULT_PROP_LIBRARY,
    load_prop_library,
    get_prop_config,
    find_props_by_category,
    find_props_by_tag,
    find_props_by_style,
    place_prop,
    populate_room,
    apply_dressing_style,
)


__version__ = "0.1.0"
__version_info__ = (0, 1, 0)

__all__ = [
    # Version
    "__version__",
    "__version_info__",
    # Enums
    "WallOrientation",
    "DoorStyle",
    "WindowStyle",
    "SwingDirection",
    "SetStyle",
    "Period",
    "PropCategory",
    "DressingStyle",
    # Config classes
    "WallConfig",
    "DoorConfig",
    "DoorPlacement",
    "WindowConfig",
    "WindowPlacement",
    "RoomConfig",
    "PropConfig",
    "PropPlacement",
    "SetConfig",
    "StylePreset",
    # Constants
    "DRESSING_STYLES",
    "DEFAULT_PROP_LIBRARY",
    # Validation
    "validate_wall_config",
    "validate_door_config",
    "validate_window_config",
    "validate_room_config",
    # Room builder
    "RoomMeshes",
    "create_room",
    "create_floor",
    "create_ceiling",
    "create_wall",
    "add_wall_opening",
    "create_molding",
    "create_wainscoting",
    "get_wall_bounds",
    # Openings
    "DoorMeshes",
    "WindowMeshes",
    "create_door",
    "create_panel_door",
    "create_flush_door",
    "create_barn_door",
    "create_french_door",
    "create_glass_door",
    "create_door_frame",
    "create_door_handle",
    "create_window",
    "create_double_hung_window",
    "create_casement_window",
    "create_picture_window",
    "create_slider_window",
    "create_window_frame",
    "create_window_sill",
    "create_curtains",
    "create_blinds",
    "place_door",
    "place_window",
    # Props
    "load_prop_library",
    "get_prop_config",
    "find_props_by_category",
    "find_props_by_tag",
    "find_props_by_style",
    "place_prop",
    "populate_room",
    "apply_dressing_style",
]
