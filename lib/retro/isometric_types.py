"""
Isometric and Side-Scroller Types

Defines dataclasses for isometric projection, side-scroller views,
sprite sheet generation, and tile-based output.

All classes designed for YAML serialization via to_dict() and
deserialization via from_dict() class methods.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum
import math


class IsometricAngle(str, Enum):
    """Isometric projection angle types."""
    TRUE_ISOMETRIC = "true_isometric"  # Equal angles (arctan(1/sqrt(2)))
    PIXEL = "pixel"                    # 2:1 pixel ratio (most common)
    MILITARY = "military"              # Planometric view
    DIMETRIC = "dimetric"              # Customizable angles


class ViewDirection(str, Enum):
    """Side-scroller view directions."""
    SIDE = "side"      # Profile view (X-axis)
    FRONT = "front"    # Front view (Y-axis)
    TOP = "top"        # Top-down view (Z-axis)


class SpriteFormat(str, Enum):
    """Sprite sheet metadata formats."""
    PHASER = "phaser"      # Phaser.js format
    UNITY = "unity"        # Unity format
    GODOT = "godot"        # Godot format
    GENERIC = "generic"    # Generic JSON format


class TileFormat(str, Enum):
    """Tile export formats."""
    PNG = "png"
    JPG = "jpg"
    BMP = "bmp"
    TGA = "tga"


# =============================================================================
# ISOMETRIC ANGLE PRESETS
# =============================================================================

ISOMETRIC_ANGLES: Dict[str, Dict[str, Any]] = {
    "true_isometric": {
        "elevation": 35.264,  # arctan(1/sqrt(2))
        "rotation": 45.0,
        "tile_ratio": (1.0, 1.0),  # Equal X and Y
        "description": "True isometric projection with equal angles",
    },
    "pixel": {
        "elevation": 30.0,  # arctan(1/2) = 26.565, rounded to 30
        "rotation": 45.0,
        "tile_ratio": (2.0, 1.0),  # 2:1 ratio
        "description": "Classic 2:1 pixel isometric (most common for games)",
    },
    "military": {
        "elevation": 45.0,
        "rotation": 45.0,
        "tile_ratio": (1.0, 1.0),
        "description": "Military/strategy game style (planometric)",
    },
    "dimetric": {
        "elevation": 30.0,
        "rotation": 30.0,
        "tile_ratio": (1.5, 1.0),
        "description": "Dimetric projection with custom angles",
    },
    "pixel_perfect": {
        "elevation": 26.565,  # Exact arctan(1/2)
        "rotation": 45.0,
        "tile_ratio": (2.0, 1.0),
        "description": "Mathematically perfect 2:1 ratio",
    },
    "blizzard": {
        "elevation": 30.0,
        "rotation": 45.0,
        "tile_ratio": (2.0, 1.0),
        "description": "Blizzard RTS style (StarCraft, Warcraft)",
    },
    "fallout": {
        "elevation": 27.0,
        "rotation": 45.0,
        "tile_ratio": (1.85, 1.0),
        "description": "Fallout 1/2 style",
    },
}


def get_isometric_angle(name: str) -> Optional[Dict[str, Any]]:
    """
    Get isometric angle preset by name.

    Args:
        name: Angle preset name

    Returns:
        Angle configuration dict or None if not found
    """
    return ISOMETRIC_ANGLES.get(name.lower().replace("-", "_"))


def list_isometric_angles() -> List[str]:
    """
    List all available isometric angle presets.

    Returns:
        List of angle preset names
    """
    return list(ISOMETRIC_ANGLES.keys())


# =============================================================================
# TILE SIZE PRESETS
# =============================================================================

TILE_SIZES: Dict[str, Tuple[int, int]] = {
    "nes": (16, 16),
    "snes": (16, 16),
    "gba": (16, 16),
    "modern_32": (32, 32),
    "modern_64": (64, 64),
    "isometric_32": (32, 16),
    "isometric_64": (64, 32),
    "isometric_128": (128, 64),
    "hd_16x16": (16, 16),
    "hd_32x32": (32, 32),
    "hd_64x64": (64, 64),
}


def get_tile_size(name: str) -> Optional[Tuple[int, int]]:
    """
    Get tile size preset by name.

    Args:
        name: Tile size preset name

    Returns:
        (width, height) tuple or None if not found
    """
    return TILE_SIZES.get(name.lower())


def list_tile_sizes() -> List[str]:
    """
    List all available tile size presets.

    Returns:
        List of tile size preset names
    """
    return list(TILE_SIZES.keys())


# =============================================================================
# ISOMETRIC CONFIG
# =============================================================================

@dataclass
class IsometricConfig:
    """
    Isometric view configuration.

    Defines settings for isometric projection rendering including
    angle presets, tile dimensions, depth sorting, and layer separation.

    Attributes:
        enabled: Whether isometric mode is enabled
        angle: Angle preset name (true_isometric, pixel, military, dimetric)
        tile_width: Width of isometric tile in pixels
        tile_height: Height of isometric tile in pixels
        depth_sorting: Enable painter's algorithm for correct rendering order
        layer_separation: List of layer names for depth sorting (ground, objects, characters)
        orthographic_scale: Orthographic camera scale factor
        custom_elevation: Custom elevation angle (overrides preset)
        custom_rotation: Custom rotation angle (overrides preset)
        snap_to_grid: Snap objects to isometric grid
        grid_visible: Show isometric grid overlay
    """
    enabled: bool = True
    angle: str = "pixel"
    tile_width: int = 32
    tile_height: int = 16
    depth_sorting: bool = True
    layer_separation: List[str] = field(default_factory=lambda: ["ground", "objects", "characters"])
    orthographic_scale: float = 10.0
    custom_elevation: Optional[float] = None
    custom_rotation: Optional[float] = None
    snap_to_grid: bool = True
    grid_visible: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "enabled": self.enabled,
            "angle": self.angle,
            "tile_width": self.tile_width,
            "tile_height": self.tile_height,
            "depth_sorting": self.depth_sorting,
            "layer_separation": self.layer_separation,
            "orthographic_scale": self.orthographic_scale,
            "custom_elevation": self.custom_elevation,
            "custom_rotation": self.custom_rotation,
            "snap_to_grid": self.snap_to_grid,
            "grid_visible": self.grid_visible,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> IsometricConfig:
        """Create from dictionary."""
        return cls(
            enabled=data.get("enabled", True),
            angle=data.get("angle", "pixel"),
            tile_width=data.get("tile_width", 32),
            tile_height=data.get("tile_height", 16),
            depth_sorting=data.get("depth_sorting", True),
            layer_separation=data.get("layer_separation", ["ground", "objects", "characters"]),
            orthographic_scale=data.get("orthographic_scale", 10.0),
            custom_elevation=data.get("custom_elevation"),
            custom_rotation=data.get("custom_rotation"),
            snap_to_grid=data.get("snap_to_grid", True),
            grid_visible=data.get("grid_visible", False),
        )

    def validate(self) -> List[str]:
        """
        Validate configuration and return list of errors.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        valid_angles = list(ISOMETRIC_ANGLES.keys())
        if self.angle.lower().replace("-", "_") not in valid_angles:
            errors.append(f"Invalid angle '{self.angle}'. Must be one of: {valid_angles}")

        if self.tile_width < 1:
            errors.append(f"tile_width must be >= 1, got {self.tile_width}")

        if self.tile_height < 1:
            errors.append(f"tile_height must be >= 1, got {self.tile_height}")

        if self.orthographic_scale <= 0:
            errors.append(f"orthographic_scale must be > 0, got {self.orthographic_scale}")

        if self.custom_elevation is not None:
            if self.custom_elevation < 0 or self.custom_elevation > 90:
                errors.append(f"custom_elevation must be 0-90 degrees, got {self.custom_elevation}")

        if self.custom_rotation is not None:
            if self.custom_rotation < 0 or self.custom_rotation > 360:
                errors.append(f"custom_rotation must be 0-360 degrees, got {self.custom_rotation}")

        return errors

    def get_angles(self) -> Tuple[float, float]:
        """
        Get elevation and rotation angles.

        Returns custom angles if set, otherwise returns preset angles.

        Returns:
            (elevation, rotation) tuple in degrees
        """
        if self.custom_elevation is not None and self.custom_rotation is not None:
            return (self.custom_elevation, self.custom_rotation)

        preset = get_isometric_angle(self.angle)
        if preset:
            return (preset["elevation"], preset["rotation"])

        # Default to pixel isometric
        return (30.0, 45.0)

    @classmethod
    def for_game_style(cls, style: str) -> IsometricConfig:
        """
        Create configuration preset for a specific game style.

        Args:
            style: Game style name (classic_pixel, strategy, blizzard, fallout)

        Returns:
            IsometricConfig configured for that style
        """
        presets = {
            "classic_pixel": cls(
                angle="pixel",
                tile_width=64,
                tile_height=32,
                depth_sorting=True,
            ),
            "true_iso": cls(
                angle="true_isometric",
                tile_width=64,
                tile_height=64,
                depth_sorting=True,
            ),
            "strategy": cls(
                angle="military",
                tile_width=64,
                tile_height=64,
                depth_sorting=False,
            ),
            "blizzard": cls(
                angle="blizzard",
                tile_width=64,
                tile_height=32,
                depth_sorting=True,
            ),
            "fallout": cls(
                angle="fallout",
                tile_width=80,
                tile_height=36,
                depth_sorting=True,
            ),
            "pixel_perfect": cls(
                angle="pixel_perfect",
                tile_width=64,
                tile_height=32,
                depth_sorting=True,
            ),
        }
        return presets.get(style.lower(), cls())


# =============================================================================
# SIDE-SCROLLER CONFIG
# =============================================================================

@dataclass
class SideScrollerConfig:
    """
    Side-scroller view configuration.

    Defines settings for side-scroller rendering with parallax layers
    and depth-based separation.

    Attributes:
        enabled: Whether side-scroller mode is enabled
        parallax_layers: Number of parallax layers (1-8)
        layer_depths: Depth values for each layer (0.0 = far, 1.0 = near)
        layer_names: Names for each layer
        orthographic: Use orthographic camera (vs perspective)
        view_direction: View direction (side, front, top)
        camera_distance: Distance from camera to subject
        auto_assign_depth: Automatically assign objects to layers based on Z
        scroll_speed: Base scroll speed multiplier
    """
    enabled: bool = True
    parallax_layers: int = 4
    layer_depths: List[float] = field(default_factory=lambda: [0.25, 0.5, 1.0, 2.0])
    layer_names: List[str] = field(default_factory=lambda: ["far_bg", "mid_bg", "near_bg", "foreground"])
    orthographic: bool = True
    view_direction: str = "side"
    camera_distance: float = 10.0
    auto_assign_depth: bool = True
    scroll_speed: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "enabled": self.enabled,
            "parallax_layers": self.parallax_layers,
            "layer_depths": self.layer_depths,
            "layer_names": self.layer_names,
            "orthographic": self.orthographic,
            "view_direction": self.view_direction,
            "camera_distance": self.camera_distance,
            "auto_assign_depth": self.auto_assign_depth,
            "scroll_speed": self.scroll_speed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SideScrollerConfig:
        """Create from dictionary."""
        return cls(
            enabled=data.get("enabled", True),
            parallax_layers=data.get("parallax_layers", 4),
            layer_depths=data.get("layer_depths", [0.25, 0.5, 1.0, 2.0]),
            layer_names=data.get("layer_names", ["far_bg", "mid_bg", "near_bg", "foreground"]),
            orthographic=data.get("orthographic", True),
            view_direction=data.get("view_direction", "side"),
            camera_distance=data.get("camera_distance", 10.0),
            auto_assign_depth=data.get("auto_assign_depth", True),
            scroll_speed=data.get("scroll_speed", 1.0),
        )

    def validate(self) -> List[str]:
        """
        Validate configuration and return list of errors.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        if self.parallax_layers < 1 or self.parallax_layers > 8:
            errors.append(f"parallax_layers must be 1-8, got {self.parallax_layers}")

        if len(self.layer_depths) != self.parallax_layers:
            errors.append(f"layer_depths length ({len(self.layer_depths)}) must match parallax_layers ({self.parallax_layers})")

        if len(self.layer_names) != self.parallax_layers:
            errors.append(f"layer_names length ({len(self.layer_names)}) must match parallax_layers ({self.parallax_layers})")

        valid_directions = ["side", "front", "top"]
        if self.view_direction not in valid_directions:
            errors.append(f"Invalid view_direction '{self.view_direction}'. Must be one of: {valid_directions}")

        if self.camera_distance <= 0:
            errors.append(f"camera_distance must be > 0, got {self.camera_distance}")

        if self.scroll_speed <= 0:
            errors.append(f"scroll_speed must be > 0, got {self.scroll_speed}")

        return errors

    def get_layer_depth(self, layer_index: int) -> float:
        """
        Get depth value for a layer.

        Args:
            layer_index: Layer index (0 = farthest)

        Returns:
            Depth value
        """
        if 0 <= layer_index < len(self.layer_depths):
            return self.layer_depths[layer_index]
        return 1.0

    def get_layer_name(self, layer_index: int) -> str:
        """
        Get name for a layer.

        Args:
            layer_index: Layer index (0 = farthest)

        Returns:
            Layer name
        """
        if 0 <= layer_index < len(self.layer_names):
            return self.layer_names[layer_index]
        return f"layer_{layer_index}"

    @classmethod
    def for_style(cls, style: str) -> SideScrollerConfig:
        """
        Create configuration preset for a specific game style.

        Args:
            style: Game style name (platformer_16bit, simple, cinematic, endless_runner)

        Returns:
            SideScrollerConfig configured for that style
        """
        presets = {
            "platformer_16bit": cls(
                parallax_layers=4,
                layer_depths=[0.1, 0.3, 0.6, 1.0],
                layer_names=["sky", "far", "mid", "near"],
                scroll_speed=1.0,
            ),
            "simple": cls(
                parallax_layers=2,
                layer_depths=[0.5, 1.0],
                layer_names=["background", "foreground"],
                scroll_speed=1.0,
            ),
            "cinematic": cls(
                parallax_layers=6,
                layer_depths=[0.1, 0.2, 0.4, 0.6, 1.0, 1.5],
                layer_names=["sky", "mountains", "far_city", "mid_city", "near_city", "foreground"],
                scroll_speed=0.8,
            ),
            "endless_runner": cls(
                parallax_layers=3,
                layer_depths=[0.3, 0.7, 1.0],
                layer_names=["bg", "mid", "fg"],
                scroll_speed=2.0,
            ),
            "minimal": cls(
                parallax_layers=1,
                layer_depths=[1.0],
                layer_names=["main"],
                scroll_speed=1.0,
            ),
        }
        return presets.get(style.lower(), cls())


# =============================================================================
# SPRITE SHEET CONFIG
# =============================================================================

@dataclass
class SpriteSheetConfig:
    """
    Sprite sheet export configuration.

    Defines settings for generating sprite sheets from animation frames
    including layout, trimming, pivot points, and metadata generation.

    Attributes:
        columns: Number of columns in sprite sheet
        rows: Number of rows in sprite sheet
        frame_width: Width of each frame in pixels
        frame_height: Height of each frame in pixels
        padding: Padding between sprites in pixels
        spacing: Spacing between sprites in pixels
        trim: Trim transparent borders from sprites
        pivot_x: Pivot point X (0.0-1.0, 0.5 = center)
        pivot_y: Pivot point Y (0.0-1.0, 0.5 = center)
        generate_json: Generate metadata JSON file
        json_format: JSON format (phaser, unity, godot, generic)
        output_format: Output image format
        power_of_two: Force power-of-two dimensions
    """
    columns: int = 8
    rows: int = 8
    frame_width: int = 32
    frame_height: int = 32
    padding: int = 0
    spacing: int = 0
    trim: bool = True
    pivot_x: float = 0.5
    pivot_y: float = 0.5
    generate_json: bool = True
    json_format: str = "phaser"
    output_format: str = "png"
    power_of_two: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "columns": self.columns,
            "rows": self.rows,
            "frame_width": self.frame_width,
            "frame_height": self.frame_height,
            "padding": self.padding,
            "spacing": self.spacing,
            "trim": self.trim,
            "pivot_x": self.pivot_x,
            "pivot_y": self.pivot_y,
            "generate_json": self.generate_json,
            "json_format": self.json_format,
            "output_format": self.output_format,
            "power_of_two": self.power_of_two,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SpriteSheetConfig:
        """Create from dictionary."""
        return cls(
            columns=data.get("columns", 8),
            rows=data.get("rows", 8),
            frame_width=data.get("frame_width", 32),
            frame_height=data.get("frame_height", 32),
            padding=data.get("padding", 0),
            spacing=data.get("spacing", 0),
            trim=data.get("trim", True),
            pivot_x=data.get("pivot_x", 0.5),
            pivot_y=data.get("pivot_y", 0.5),
            generate_json=data.get("generate_json", True),
            json_format=data.get("json_format", "phaser"),
            output_format=data.get("output_format", "png"),
            power_of_two=data.get("power_of_two", False),
        )

    def validate(self) -> List[str]:
        """
        Validate configuration and return list of errors.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        if self.columns < 1:
            errors.append(f"columns must be >= 1, got {self.columns}")

        if self.rows < 1:
            errors.append(f"rows must be >= 1, got {self.rows}")

        if self.frame_width < 1:
            errors.append(f"frame_width must be >= 1, got {self.frame_width}")

        if self.frame_height < 1:
            errors.append(f"frame_height must be >= 1, got {self.frame_height}")

        if self.padding < 0:
            errors.append(f"padding must be >= 0, got {self.padding}")

        if self.spacing < 0:
            errors.append(f"spacing must be >= 0, got {self.spacing}")

        if self.pivot_x < 0 or self.pivot_x > 1:
            errors.append(f"pivot_x must be 0.0-1.0, got {self.pivot_x}")

        if self.pivot_y < 0 or self.pivot_y > 1:
            errors.append(f"pivot_y must be 0.0-1.0, got {self.pivot_y}")

        valid_formats = ["phaser", "unity", "godot", "generic"]
        if self.json_format not in valid_formats:
            errors.append(f"Invalid json_format '{self.json_format}'. Must be one of: {valid_formats}")

        valid_output = ["png", "jpg", "bmp", "tga"]
        if self.output_format not in valid_output:
            errors.append(f"Invalid output_format '{self.output_format}'. Must be one of: {valid_output}")

        return errors

    def get_sheet_size(self, frame_count: int = 0) -> Tuple[int, int]:
        """
        Calculate sprite sheet dimensions.

        Args:
            frame_count: Number of frames (if 0, uses columns * rows)

        Returns:
            (width, height) tuple in pixels
        """
        if frame_count > 0:
            # Calculate optimal layout
            cols = min(frame_count, self.columns)
            rows = math.ceil(frame_count / cols)
        else:
            cols = self.columns
            rows = self.rows

        width = cols * self.frame_width + (cols - 1) * self.spacing + 2 * self.padding
        height = rows * self.frame_height + (rows - 1) * self.spacing + 2 * self.padding

        if self.power_of_two:
            width = 2 ** math.ceil(math.log2(width))
            height = 2 ** math.ceil(math.log2(height))

        return (width, height)

    @classmethod
    def for_character(cls, frame_width: int = 32, frame_height: int = 32) -> SpriteSheetConfig:
        """
        Create configuration for character sprite sheet.

        Args:
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels

        Returns:
            SpriteSheetConfig for character
        """
        return cls(
            columns=8,
            rows=4,
            frame_width=frame_width,
            frame_height=frame_height,
            trim=True,
            json_format="phaser",
        )

    @classmethod
    def for_tileset(cls, tile_size: int = 16) -> SpriteSheetConfig:
        """
        Create configuration for tile set.

        Args:
            tile_size: Tile size in pixels

        Returns:
            SpriteSheetConfig for tile set
        """
        return cls(
            columns=16,
            rows=16,
            frame_width=tile_size,
            frame_height=tile_size,
            trim=False,
            spacing=0,
            power_of_two=True,
        )


# =============================================================================
# TILE CONFIG
# =============================================================================

@dataclass
class TileConfig:
    """
    Tile export configuration.

    Defines settings for tile-based output including tile dimensions,
    spacing, and export format.

    Attributes:
        tile_size: Tile dimensions (width, height) in pixels
        padding: Padding around each tile in pixels
        spacing: Spacing between tiles in pixels
        format: Output image format
        generate_map: Generate tile map data file
        map_format: Tile map format (csv, json, tmx)
        collision_layer: Generate collision layer data
        autotile: Generate autotile (blob tile) templates
    """
    tile_size: Tuple[int, int] = (32, 32)
    padding: int = 0
    spacing: int = 0
    format: str = "png"
    generate_map: bool = True
    map_format: str = "csv"
    collision_layer: bool = False
    autotile: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "tile_size": list(self.tile_size),
            "padding": self.padding,
            "spacing": self.spacing,
            "format": self.format,
            "generate_map": self.generate_map,
            "map_format": self.map_format,
            "collision_layer": self.collision_layer,
            "autotile": self.autotile,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TileConfig:
        """Create from dictionary."""
        return cls(
            tile_size=tuple(data.get("tile_size", (32, 32))),
            padding=data.get("padding", 0),
            spacing=data.get("spacing", 0),
            format=data.get("format", "png"),
            generate_map=data.get("generate_map", True),
            map_format=data.get("map_format", "csv"),
            collision_layer=data.get("collision_layer", False),
            autotile=data.get("autotile", False),
        )

    def validate(self) -> List[str]:
        """
        Validate configuration and return list of errors.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        if self.tile_size[0] < 1 or self.tile_size[1] < 1:
            errors.append(f"tile_size must be >= (1, 1), got {self.tile_size}")

        if self.padding < 0:
            errors.append(f"padding must be >= 0, got {self.padding}")

        if self.spacing < 0:
            errors.append(f"spacing must be >= 0, got {self.spacing}")

        valid_formats = ["png", "jpg", "bmp", "tga"]
        if self.format not in valid_formats:
            errors.append(f"Invalid format '{self.format}'. Must be one of: {valid_formats}")

        valid_map_formats = ["csv", "json", "tmx"]
        if self.map_format not in valid_map_formats:
            errors.append(f"Invalid map_format '{self.map_format}'. Must be one of: {valid_map_formats}")

        return errors

    @classmethod
    def for_console(cls, console: str) -> TileConfig:
        """
        Create configuration preset for a specific console.

        Args:
            console: Console name (nes, snes, gba, modern)

        Returns:
            TileConfig configured for that console
        """
        presets = {
            "nes": cls(
                tile_size=(16, 16),
                generate_map=True,
                map_format="csv",
            ),
            "snes": cls(
                tile_size=(16, 16),
                generate_map=True,
                map_format="csv",
            ),
            "gba": cls(
                tile_size=(16, 16),
                generate_map=True,
                map_format="json",
            ),
            "modern": cls(
                tile_size=(32, 32),
                generate_map=True,
                map_format="tmx",
                autotile=True,
            ),
        }
        return presets.get(console.lower(), cls())

    @classmethod
    def for_isometric(cls, style: str = "pixel") -> TileConfig:
        """
        Create configuration for isometric tiles.

        Args:
            style: Isometric style (pixel, true_iso)

        Returns:
            TileConfig for isometric tiles
        """
        if style == "pixel":
            return cls(
                tile_size=(32, 16),
                generate_map=True,
                map_format="json",
            )
        else:
            return cls(
                tile_size=(32, 32),
                generate_map=True,
                map_format="json",
            )


# =============================================================================
# RESULT TYPES
# =============================================================================

@dataclass
class IsometricRenderResult:
    """
    Result of isometric rendering.

    Contains the rendered image and metadata about the isometric projection.

    Attributes:
        image: Rendered isometric image (PIL Image or numpy array)
        tile_count: Number of tiles rendered
        camera_angles: (elevation, rotation) used for rendering
        sorted_objects: List of object names in depth-sorted order
        warnings: Any warnings generated during rendering
    """
    image: Any = None
    tile_count: int = 0
    camera_angles: Tuple[float, float] = (30.0, 45.0)
    sorted_objects: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization (without image data)."""
        return {
            "tile_count": self.tile_count,
            "camera_angles": list(self.camera_angles),
            "sorted_objects": self.sorted_objects,
            "warnings": self.warnings,
        }


@dataclass
class SpriteSheetResult:
    """
    Result of sprite sheet generation.

    Contains the sprite sheet image and metadata.

    Attributes:
        image: Sprite sheet image (PIL Image or numpy array)
        metadata: Generated metadata dict (format depends on json_format)
        frame_count: Number of frames in sheet
        sheet_size: (width, height) of sprite sheet
        trimmed_count: Number of frames that were trimmed
        warnings: Any warnings generated during generation
    """
    image: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    frame_count: int = 0
    sheet_size: Tuple[int, int] = (0, 0)
    trimmed_count: int = 0
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization (without image data)."""
        return {
            "frame_count": self.frame_count,
            "sheet_size": list(self.sheet_size),
            "trimmed_count": self.trimmed_count,
            "warnings": self.warnings,
        }


@dataclass
class TileSetResult:
    """
    Result of tile set generation.

    Contains the tile set image and tile map data.

    Attributes:
        image: Tile set image (PIL Image or numpy array)
        tile_map: 2D array of tile indices
        tile_count: Number of unique tiles
        collision_map: Optional collision layer data
        warnings: Any warnings generated during generation
    """
    image: Any = None
    tile_map: List[List[int]] = field(default_factory=list)
    tile_count: int = 0
    collision_map: Optional[List[List[int]]] = None
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization (without image data)."""
        return {
            "tile_count": self.tile_count,
            "tile_map": self.tile_map,
            "collision_map": self.collision_map,
            "warnings": self.warnings,
        }
