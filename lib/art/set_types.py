"""
Set Builder Types

Data structures for procedural set construction including walls,
rooms, doors, windows, props, and style presets.

Implements REQ-SET-01 through REQ-SET-05.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum


class WallOrientation(Enum):
    """Wall orientation within a room."""
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"


class DoorStyle(Enum):
    """Door style types."""
    PANEL_6 = "panel_6"  # Classic 6-panel door
    PANEL_4 = "panel_4"  # 4-panel door
    FLUSH = "flush"  # Flat/flush door
    BARN = "barn"  # Sliding barn door
    FRENCH = "french"  # French door with glass panes
    POCKET = "pocket"  # Pocket sliding door
    DUTCH = "dutch"  # Split horizontally
    LOUVER = "louver"  # Vented louver door
    GLASS = "glass"  # Full glass door


class WindowStyle(Enum):
    """Window style types."""
    DOUBLE_HUNG = "double_hung"  # Two sashes that slide up/down
    SINGLE_HUNG = "single_hung"  # One movable sash
    CASEMENT = "casement"  # Hinged, opens outward
    AWNING = "awning"  # Hinged at top, opens outward
    PICTURE = "picture"  # Fixed, non-opening
    BAY = "bay"  # Projects outward from wall
    BOW = "bow"  # Curved bay window
    SLIDER = "slider"  # Slides horizontally
    SKYLIGHT = "skylight"  # Roof window


class SwingDirection(Enum):
    """Door swing direction."""
    IN_LEFT = "in_left"  # Opens inward, hinges on left
    IN_RIGHT = "in_right"  # Opens inward, hinges on right
    OUT_LEFT = "out_left"  # Opens outward, hinges on left
    OUT_RIGHT = "out_right"  # Opens outward, hinges on right
    SLIDE_LEFT = "slide_left"  # Slides to left
    SLIDE_RIGHT = "slide_right"  # Slides to right


class SetStyle(Enum):
    """Overall set style presets."""
    MODERN_RESIDENTIAL = "modern_residential"
    VICTORIAN = "victorian"
    INDUSTRIAL = "industrial"
    OFFICE = "office"
    CORPORATE = "corporate"
    MINIMALIST = "minimalist"
    SCANDINAVIAN = "scandinavian"
    MID_CENTURY = "mid_century"
    ART_DECO = "art_deco"
    BRUTALIST = "brutalist"


class Period(Enum):
    """Time period presets for set design."""
    PRESENT = "present"
    FUTURE = "future"
    NEAR_FUTURE = "near_future"
    CYBERPUNK = "cyberpunk"
    RETRO_FUTURE = "retro_future"
    MODERNIST_1960S = "1960s"
    MID_CENTURY_1950S = "1950s"
    POST_WAR_1940S = "1940s"
    ART_DECO_1920S = "1920s"
    VICTORIAN_1890S = "1890s"
    GEORGIAN_1800S = "1800s"


class PropCategory(Enum):
    """Prop category types."""
    FURNITURE = "furniture"
    DECOR = "decor"
    ELECTRONICS = "electronics"
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"
    LIGHTING = "lighting"
    PLANTS = "plants"
    BOOKS = "books"
    ART = "art"
    TEXTILES = "textiles"
    STORAGE = "storage"
    APPLIANCES = "appliances"


class DressingStyle(Enum):
    """Room dressing style presets."""
    MINIMAL = "minimal"
    LIVED_IN = "lived_in"
    CLUTTERED = "cluttered"
    STERILE = "sterile"
    ECLECTIC = "eclectic"
    STAGED = "staged"
    ABANDONED = "abandoned"
    HOARDER = "hoarder"


# =============================================================================
# WALL CONFIGURATION
# =============================================================================

@dataclass
class WallConfig:
    """
    Wall configuration.

    Attributes:
        width: Wall width in meters
        height: Wall height in meters
        thickness: Wall thickness in meters
        material: Material preset name
        baseboard_height: Baseboard height in meters
        baseboard_material: Baseboard material preset
        crown_molding: Whether crown molding is present
        crown_molding_height: Crown molding height in meters
        crown_molding_material: Crown molding material preset
        chair_rail: Whether chair rail is present
        chair_rail_height: Chair rail height in meters
        wainscoting: Whether wainscoting is present
        wainscoting_height: Wainscoting height in meters
        wainscoting_material: Wainscoting material preset
        wallpaper: Whether wallpaper is applied
        wallpaper_pattern: Wallpaper pattern name
        color: Wall paint color (RGB 0-1)
    """
    width: float = 4.0  # meters
    height: float = 2.8  # Standard ceiling height
    thickness: float = 0.15  # Standard interior wall
    material: str = "drywall_white"
    baseboard_height: float = 0.1
    baseboard_material: str = "wood_white"
    crown_molding: bool = False
    crown_molding_height: float = 0.08
    crown_molding_material: str = "wood_white"
    chair_rail: bool = False
    chair_rail_height: float = 0.9
    wainscoting: bool = False
    wainscoting_height: float = 1.0
    wainscoting_material: str = "wood_white"
    wallpaper: bool = False
    wallpaper_pattern: str = ""
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "width": self.width,
            "height": self.height,
            "thickness": self.thickness,
            "material": self.material,
            "baseboard_height": self.baseboard_height,
            "baseboard_material": self.baseboard_material,
            "crown_molding": self.crown_molding,
            "crown_molding_height": self.crown_molding_height,
            "crown_molding_material": self.crown_molding_material,
            "chair_rail": self.chair_rail,
            "chair_rail_height": self.chair_rail_height,
            "wainscoting": self.wainscoting,
            "wainscoting_height": self.wainscoting_height,
            "wainscoting_material": self.wainscoting_material,
            "wallpaper": self.wallpaper,
            "wallpaper_pattern": self.wallpaper_pattern,
            "color": list(self.color),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WallConfig":
        """Create from dictionary."""
        return cls(
            width=data.get("width", 4.0),
            height=data.get("height", 2.8),
            thickness=data.get("thickness", 0.15),
            material=data.get("material", "drywall_white"),
            baseboard_height=data.get("baseboard_height", 0.1),
            baseboard_material=data.get("baseboard_material", "wood_white"),
            crown_molding=data.get("crown_molding", False),
            crown_molding_height=data.get("crown_molding_height", 0.08),
            crown_molding_material=data.get("crown_molding_material", "wood_white"),
            chair_rail=data.get("chair_rail", False),
            chair_rail_height=data.get("chair_rail_height", 0.9),
            wainscoting=data.get("wainscoting", False),
            wainscoting_height=data.get("wainscoting_height", 1.0),
            wainscoting_material=data.get("wainscoting_material", "wood_white"),
            wallpaper=data.get("wallpaper", False),
            wallpaper_pattern=data.get("wallpaper_pattern", ""),
            color=tuple(data.get("color", (1.0, 1.0, 1.0))),
        )


# =============================================================================
# DOOR CONFIGURATION
# =============================================================================

@dataclass
class DoorConfig:
    """
    Door configuration.

    Attributes:
        width: Door width in meters
        height: Door height in meters
        thickness: Door thickness in meters
        style: Door style preset
        material: Door material preset
        frame_material: Door frame material
        handle_style: Handle/hardware style
        handle_material: Handle material (brass, chrome, etc.)
        swing_direction: Door swing direction
        has_transom: Whether transom window above door
        has_sidelights: Whether sidelights on sides
        glass_type: Glass type for doors with glass
        color: Door paint color (RGB 0-1)
    """
    width: float = 0.9  # Standard door width
    height: float = 2.1  # Standard door height
    thickness: float = 0.04  # Standard door thickness
    style: str = "panel_6"
    material: str = "wood_oak"
    frame_material: str = "wood_oak"
    handle_style: str = "lever_modern"
    handle_material: str = "chrome"
    swing_direction: str = "in_left"
    has_transom: bool = False
    has_sidelights: bool = False
    glass_type: str = "clear"  # clear, frosted, seeded
    color: Tuple[float, float, float] = (0.6, 0.4, 0.2)  # Wood tone

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "width": self.width,
            "height": self.height,
            "thickness": self.thickness,
            "style": self.style,
            "material": self.material,
            "frame_material": self.frame_material,
            "handle_style": self.handle_style,
            "handle_material": self.handle_material,
            "swing_direction": self.swing_direction,
            "has_transom": self.has_transom,
            "has_sidelights": self.has_sidelights,
            "glass_type": self.glass_type,
            "color": list(self.color),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DoorConfig":
        """Create from dictionary."""
        return cls(
            width=data.get("width", 0.9),
            height=data.get("height", 2.1),
            thickness=data.get("thickness", 0.04),
            style=data.get("style", "panel_6"),
            material=data.get("material", "wood_oak"),
            frame_material=data.get("frame_material", "wood_oak"),
            handle_style=data.get("handle_style", "lever_modern"),
            handle_material=data.get("handle_material", "chrome"),
            swing_direction=data.get("swing_direction", "in_left"),
            has_transom=data.get("has_transom", False),
            has_sidelights=data.get("has_sidelights", False),
            glass_type=data.get("glass_type", "clear"),
            color=tuple(data.get("color", (0.6, 0.4, 0.2))),
        )


@dataclass
class DoorPlacement:
    """
    Door placement configuration within a room.

    Attributes:
        wall: Wall orientation (north, south, east, west)
        position: Position along wall (0-1 normalized)
        offset_from_floor: Height offset from floor (for non-standard placement)
        config: Door configuration
        name: Door identifier
    """
    wall: str = "north"
    position: float = 0.5  # Center of wall
    offset_from_floor: float = 0.0
    config: DoorConfig = field(default_factory=DoorConfig)
    name: str = "door_01"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "wall": self.wall,
            "position": self.position,
            "offset_from_floor": self.offset_from_floor,
            "config": self.config.to_dict(),
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DoorPlacement":
        """Create from dictionary."""
        config_data = data.get("config", {})
        return cls(
            wall=data.get("wall", "north"),
            position=data.get("position", 0.5),
            offset_from_floor=data.get("offset_from_floor", 0.0),
            config=DoorConfig.from_dict(config_data),
            name=data.get("name", "door_01"),
        )


# =============================================================================
# WINDOW CONFIGURATION
# =============================================================================

@dataclass
class WindowConfig:
    """
    Window configuration.

    Attributes:
        width: Window width in meters
        height: Window height in meters
        depth: Window depth/thickness in meters
        sill_height: Height of window sill from floor
        style: Window style preset
        frame_material: Frame material preset
        frame_width: Frame width in meters
        has_curtains: Whether curtains are present
        curtain_style: Curtain style (panel, rod, blind, shade)
        curtain_material: Curtain material/fabric
        curtain_color: Curtain color (RGB 0-1)
        has_blinds: Whether blinds are present
        blind_type: Blind type (venetian, vertical, roller)
        glass_type: Glass type (clear, tinted, frosted, low_e)
        num_panes: Number of glass panes (for divided light)
        has_shutters: Whether exterior shutters are present
        shutter_color: Shutter color (RGB 0-1)
    """
    width: float = 1.2
    height: float = 1.4
    depth: float = 0.1
    sill_height: float = 0.9  # Standard sill height
    style: str = "double_hung"
    frame_material: str = "wood_white"
    frame_width: float = 0.05
    has_curtains: bool = False
    curtain_style: str = "panel"
    curtain_material: str = "fabric_cotton"
    curtain_color: Tuple[float, float, float] = (0.9, 0.9, 0.9)
    has_blinds: bool = False
    blind_type: str = "venetian"
    glass_type: str = "clear"
    num_panes: int = 1  # Single pane default
    has_shutters: bool = False
    shutter_color: Tuple[float, float, float] = (0.3, 0.3, 0.3)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "width": self.width,
            "height": self.height,
            "depth": self.depth,
            "sill_height": self.sill_height,
            "style": self.style,
            "frame_material": self.frame_material,
            "frame_width": self.frame_width,
            "has_curtains": self.has_curtains,
            "curtain_style": self.curtain_style,
            "curtain_material": self.curtain_material,
            "curtain_color": list(self.curtain_color),
            "has_blinds": self.has_blinds,
            "blind_type": self.blind_type,
            "glass_type": self.glass_type,
            "num_panes": self.num_panes,
            "has_shutters": self.has_shutters,
            "shutter_color": list(self.shutter_color),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WindowConfig":
        """Create from dictionary."""
        return cls(
            width=data.get("width", 1.2),
            height=data.get("height", 1.4),
            depth=data.get("depth", 0.1),
            sill_height=data.get("sill_height", 0.9),
            style=data.get("style", "double_hung"),
            frame_material=data.get("frame_material", "wood_white"),
            frame_width=data.get("frame_width", 0.05),
            has_curtains=data.get("has_curtains", False),
            curtain_style=data.get("curtain_style", "panel"),
            curtain_material=data.get("curtain_material", "fabric_cotton"),
            curtain_color=tuple(data.get("curtain_color", (0.9, 0.9, 0.9))),
            has_blinds=data.get("has_blinds", False),
            blind_type=data.get("blind_type", "venetian"),
            glass_type=data.get("glass_type", "clear"),
            num_panes=data.get("num_panes", 1),
            has_shutters=data.get("has_shutters", False),
            shutter_color=tuple(data.get("shutter_color", (0.3, 0.3, 0.3))),
        )


@dataclass
class WindowPlacement:
    """
    Window placement configuration within a room.

    Attributes:
        wall: Wall orientation (north, south, east, west)
        position: Position along wall (0-1 normalized)
        height: Height from floor to sill
        config: Window configuration
        name: Window identifier
    """
    wall: str = "south"
    position: float = 0.5  # Center of wall
    height: float = 0.9  # Sill height
    config: WindowConfig = field(default_factory=WindowConfig)
    name: str = "window_01"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "wall": self.wall,
            "position": self.position,
            "height": self.height,
            "config": self.config.to_dict(),
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WindowPlacement":
        """Create from dictionary."""
        config_data = data.get("config", {})
        return cls(
            wall=data.get("wall", "south"),
            position=data.get("position", 0.5),
            height=data.get("height", 0.9),
            config=WindowConfig.from_dict(config_data),
            name=data.get("name", "window_01"),
        )


# =============================================================================
# ROOM CONFIGURATION
# =============================================================================

@dataclass
class RoomConfig:
    """
    Room configuration.

    Attributes:
        name: Room name/identifier
        width: Room width in meters (X dimension)
        depth: Room depth in meters (Y dimension)
        height: Room height in meters (Z dimension)
        floor_material: Floor material preset
        ceiling_material: Ceiling material preset
        walls: Dictionary of wall configurations by orientation
        doors: List of door placements
        windows: List of window placements
        has_crown_molding: Whether crown molding is present
        has_baseboard: Whether baseboard is present
        floor_thickness: Floor thickness in meters
        ceiling_thickness: Ceiling thickness in meters
    """
    name: str = "room_01"
    width: float = 5.0
    depth: float = 4.0
    height: float = 2.8
    floor_material: str = "hardwood_oak"
    ceiling_material: str = "drywall_white"
    walls: Dict[str, WallConfig] = field(default_factory=dict)
    doors: List[DoorPlacement] = field(default_factory=list)
    windows: List[WindowPlacement] = field(default_factory=list)
    has_crown_molding: bool = False
    has_baseboard: bool = True
    floor_thickness: float = 0.02
    ceiling_thickness: float = 0.02

    def __post_init__(self):
        """Initialize default walls if not provided."""
        if not self.walls:
            # Create default wall configs for each orientation
            default_wall = WallConfig(width=self.width, height=self.height)
            side_wall = WallConfig(width=self.depth, height=self.height)

            self.walls = {
                "north": WallConfig(**{**default_wall.to_dict(), "width": self.width}),
                "south": WallConfig(**{**default_wall.to_dict(), "width": self.width}),
                "east": WallConfig(**{**side_wall.to_dict(), "width": self.depth}),
                "west": WallConfig(**{**side_wall.to_dict(), "width": self.depth}),
            }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "width": self.width,
            "depth": self.depth,
            "height": self.height,
            "floor_material": self.floor_material,
            "ceiling_material": self.ceiling_material,
            "walls": {k: v.to_dict() for k, v in self.walls.items()},
            "doors": [d.to_dict() for d in self.doors],
            "windows": [w.to_dict() for w in self.windows],
            "has_crown_molding": self.has_crown_molding,
            "has_baseboard": self.has_baseboard,
            "floor_thickness": self.floor_thickness,
            "ceiling_thickness": self.ceiling_thickness,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RoomConfig":
        """Create from dictionary."""
        walls_data = data.get("walls", {})
        walls = {k: WallConfig.from_dict(v) for k, v in walls_data.items()}

        doors_data = data.get("doors", [])
        doors = [DoorPlacement.from_dict(d) for d in doors_data]

        windows_data = data.get("windows", [])
        windows = [WindowPlacement.from_dict(w) for w in windows_data]

        return cls(
            name=data.get("name", "room_01"),
            width=data.get("width", 5.0),
            depth=data.get("depth", 4.0),
            height=data.get("height", 2.8),
            floor_material=data.get("floor_material", "hardwood_oak"),
            ceiling_material=data.get("ceiling_material", "drywall_white"),
            walls=walls,
            doors=doors,
            windows=windows,
            has_crown_molding=data.get("has_crown_molding", False),
            has_baseboard=data.get("has_baseboard", True),
            floor_thickness=data.get("floor_thickness", 0.02),
            ceiling_thickness=data.get("ceiling_thickness", 0.02),
        )


# =============================================================================
# PROP CONFIGURATION
# =============================================================================

@dataclass
class PropConfig:
    """
    Prop definition configuration.

    Attributes:
        name: Prop name/identifier
        category: Prop category
        style: Style preset
        material: Default material preset
        scale: Default scale factor
        dimensions: Default dimensions (width, depth, height)
        variations: Number of available variations
        tags: Search/tags for prop lookup
    """
    name: str = ""
    category: str = "decor"
    style: str = "modern"
    material: str = "generic"
    scale: float = 1.0
    dimensions: Tuple[float, float, float] = (0.5, 0.5, 0.5)
    variations: int = 1
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "category": self.category,
            "style": self.style,
            "material": self.material,
            "scale": self.scale,
            "dimensions": list(self.dimensions),
            "variations": self.variations,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PropConfig":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            category=data.get("category", "decor"),
            style=data.get("style", "modern"),
            material=data.get("material", "generic"),
            scale=data.get("scale", 1.0),
            dimensions=tuple(data.get("dimensions", (0.5, 0.5, 0.5))),
            variations=data.get("variations", 1),
            tags=data.get("tags", []),
        )


@dataclass
class PropPlacement:
    """
    Prop placement in set.

    Attributes:
        prop: Prop name or preset
        position: World position (x, y, z)
        rotation: Rotation in Euler degrees (x, y, z)
        scale: Scale multiplier
        variant: Variant index (0-based)
        material_override: Override material preset
        custom_name: Custom object name in scene
    """
    prop: str = ""
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    scale: float = 1.0
    variant: int = 0
    material_override: str = ""
    custom_name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "prop": self.prop,
            "position": list(self.position),
            "rotation": list(self.rotation),
            "scale": self.scale,
            "variant": self.variant,
            "material_override": self.material_override,
            "custom_name": self.custom_name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PropPlacement":
        """Create from dictionary."""
        return cls(
            prop=data.get("prop", ""),
            position=tuple(data.get("position", (0.0, 0.0, 0.0))),
            rotation=tuple(data.get("rotation", (0.0, 0.0, 0.0))),
            scale=data.get("scale", 1.0),
            variant=data.get("variant", 0),
            material_override=data.get("material_override", ""),
            custom_name=data.get("custom_name", ""),
        )


# =============================================================================
# DRESSING STYLES
# =============================================================================

DRESSING_STYLES = {
    "minimal": {
        "prop_density": 0.3,
        "clutter": 0.1,
        "description": "Sparse, clean aesthetic",
    },
    "lived_in": {
        "prop_density": 0.7,
        "clutter": 0.5,
        "description": "Comfortable, realistic daily use",
    },
    "cluttered": {
        "prop_density": 0.9,
        "clutter": 0.8,
        "description": "Messy, disorganized",
    },
    "sterile": {
        "prop_density": 0.2,
        "clutter": 0.0,
        "description": "Hospital/clean room aesthetic",
    },
    "eclectic": {
        "prop_density": 0.8,
        "clutter": 0.4,
        "description": "Mixed styles, curated chaos",
    },
    "staged": {
        "prop_density": 0.5,
        "clutter": 0.1,
        "description": "Real estate staging, intentional",
    },
    "abandoned": {
        "prop_density": 0.6,
        "clutter": 0.9,
        "description": "Dusty, disheveled, decayed",
    },
    "hoarder": {
        "prop_density": 1.0,
        "clutter": 1.0,
        "description": "Extreme clutter, barely navigable",
    },
}


# =============================================================================
# SET CONFIGURATION
# =============================================================================

@dataclass
class SetConfig:
    """
    Complete set configuration.

    Attributes:
        name: Set name/identifier
        style: Overall style preset
        period: Time period preset
        rooms: List of room configurations
        props: List of prop placements
        lighting_type: Primary lighting type
        time_of_day: Time of day for lighting
        exterior_visibility: Whether exterior is visible through windows
        weather: Weather conditions
        description: Human-readable description
    """
    name: str = "set_01"
    style: str = "modern_residential"
    period: str = "present"
    rooms: List[RoomConfig] = field(default_factory=list)
    props: List[PropPlacement] = field(default_factory=list)
    lighting_type: str = "natural"  # natural, artificial, mixed
    time_of_day: str = "day"  # day, night, dawn, dusk, golden_hour
    exterior_visibility: bool = True
    weather: str = "clear"  # clear, overcast, rainy, stormy
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "style": self.style,
            "period": self.period,
            "rooms": [r.to_dict() for r in self.rooms],
            "props": [p.to_dict() for p in self.props],
            "lighting_type": self.lighting_type,
            "time_of_day": self.time_of_day,
            "exterior_visibility": self.exterior_visibility,
            "weather": self.weather,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SetConfig":
        """Create from dictionary."""
        rooms_data = data.get("rooms", [])
        rooms = [RoomConfig.from_dict(r) for r in rooms_data]

        props_data = data.get("props", [])
        props = [PropPlacement.from_dict(p) for p in props_data]

        return cls(
            name=data.get("name", "set_01"),
            style=data.get("style", "modern_residential"),
            period=data.get("period", "present"),
            rooms=rooms,
            props=props,
            lighting_type=data.get("lighting_type", "natural"),
            time_of_day=data.get("time_of_day", "day"),
            exterior_visibility=data.get("exterior_visibility", True),
            weather=data.get("weather", "clear"),
            description=data.get("description", ""),
        )


# =============================================================================
# STYLE PRESET
# =============================================================================

@dataclass
class StylePreset:
    """
    Complete style preset for set building.

    Attributes:
        name: Preset name
        style: Style category
        period: Time period
        description: Human-readable description
        default_materials: Default material assignments
        default_props: Default prop categories and styles
        wall_config: Default wall configuration
        door_config: Default door configuration
        window_config: Default window configuration
        color_palette: Default color palette (RGB values)
    """
    name: str = ""
    style: str = "modern_residential"
    period: str = "present"
    description: str = ""
    default_materials: Dict[str, str] = field(default_factory=dict)
    default_props: List[Dict[str, str]] = field(default_factory=list)
    wall_config: Optional[WallConfig] = None
    door_config: Optional[DoorConfig] = None
    window_config: Optional[WindowConfig] = None
    color_palette: List[Tuple[float, float, float]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "style": self.style,
            "period": self.period,
            "description": self.description,
            "default_materials": self.default_materials,
            "default_props": self.default_props,
            "wall_config": self.wall_config.to_dict() if self.wall_config else None,
            "door_config": self.door_config.to_dict() if self.door_config else None,
            "window_config": self.window_config.to_dict() if self.window_config else None,
            "color_palette": [list(c) for c in self.color_palette],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StylePreset":
        """Create from dictionary."""
        wall_data = data.get("wall_config")
        wall_config = WallConfig.from_dict(wall_data) if wall_data else None

        door_data = data.get("door_config")
        door_config = DoorConfig.from_dict(door_data) if door_data else None

        window_data = data.get("window_config")
        window_config = WindowConfig.from_dict(window_data) if window_data else None

        palette_data = data.get("color_palette", [])
        color_palette = [tuple(c) for c in palette_data]

        return cls(
            name=data.get("name", ""),
            style=data.get("style", "modern_residential"),
            period=data.get("period", "present"),
            description=data.get("description", ""),
            default_materials=data.get("default_materials", {}),
            default_props=data.get("default_props", []),
            wall_config=wall_config,
            door_config=door_config,
            window_config=window_config,
            color_palette=color_palette,
        )


# =============================================================================
# VALIDATION
# =============================================================================

def validate_wall_config(config: WallConfig) -> List[str]:
    """Validate wall configuration, return list of errors."""
    errors = []

    if config.width <= 0:
        errors.append("Wall width must be positive")
    if config.height <= 0:
        errors.append("Wall height must be positive")
    if config.thickness <= 0:
        errors.append("Wall thickness must be positive")
    if config.baseboard_height < 0:
        errors.append("Baseboard height cannot be negative")
    if config.crown_molding_height < 0:
        errors.append("Crown molding height cannot be negative")

    return errors


def validate_door_config(config: DoorConfig) -> List[str]:
    """Validate door configuration, return list of errors."""
    errors = []

    if config.width <= 0:
        errors.append("Door width must be positive")
    if config.height <= 0:
        errors.append("Door height must be positive")
    if config.thickness <= 0:
        errors.append("Door thickness must be positive")

    valid_styles = [s.value for s in DoorStyle]
    if config.style not in valid_styles:
        errors.append(f"Invalid door style: {config.style}")

    valid_swings = [s.value for s in SwingDirection]
    if config.swing_direction not in valid_swings:
        errors.append(f"Invalid swing direction: {config.swing_direction}")

    return errors


def validate_window_config(config: WindowConfig) -> List[str]:
    """Validate window configuration, return list of errors."""
    errors = []

    if config.width <= 0:
        errors.append("Window width must be positive")
    if config.height <= 0:
        errors.append("Window height must be positive")
    if config.sill_height < 0:
        errors.append("Window sill height cannot be negative")
    if config.num_panes < 1:
        errors.append("Window must have at least 1 pane")

    valid_styles = [s.value for s in WindowStyle]
    if config.style not in valid_styles:
        errors.append(f"Invalid window style: {config.style}")

    return errors


def validate_room_config(config: RoomConfig) -> List[str]:
    """Validate room configuration, return list of errors."""
    errors = []

    if config.width <= 0:
        errors.append("Room width must be positive")
    if config.depth <= 0:
        errors.append("Room depth must be positive")
    if config.height <= 0:
        errors.append("Room height must be positive")

    # Validate walls
    for orientation, wall in config.walls.items():
        wall_errors = validate_wall_config(wall)
        for err in wall_errors:
            errors.append(f"Wall {orientation}: {err}")

    # Validate doors
    for i, door in enumerate(config.doors):
        door_errors = validate_door_config(door.config)
        for err in door_errors:
            errors.append(f"Door {i}: {err}")

        if door.position < 0 or door.position > 1:
            errors.append(f"Door {i}: position must be between 0 and 1")

    # Validate windows
    for i, window in enumerate(config.windows):
        window_errors = validate_window_config(window.config)
        for err in window_errors:
            errors.append(f"Window {i}: {err}")

        if window.position < 0 or window.position > 1:
            errors.append(f"Window {i}: position must be between 0 and 1")

    return errors


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "WallOrientation",
    "DoorStyle",
    "WindowStyle",
    "SwingDirection",
    "SetStyle",
    "Period",
    "PropCategory",
    "DressingStyle",
    # Dataclasses
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
    # Validation
    "validate_wall_config",
    "validate_door_config",
    "validate_window_config",
    "validate_room_config",
]
