"""
View Preset Loader

Loads isometric, side-scroller, sprite sheet, and tile presets
from YAML configuration files.
"""

from __future__ import annotations
from typing import Dict, Any, Optional, List
import os

from lib.retro.isometric_types import (
    IsometricConfig,
    SideScrollerConfig,
    SpriteSheetConfig,
    TileConfig,
)


# Default preset file path
DEFAULT_PRESET_PATH = "configs/cinematic/retro/view_presets.yaml"

# Cached presets
_cached_presets: Optional[Dict[str, Any]] = None


def _load_presets_file() -> Dict[str, Any]:
    """
    Load presets from YAML file.

    Returns:
        Dict with all preset categories
    """
    global _cached_presets

    if _cached_presets is not None:
        return _cached_presets

    try:
        import yaml
    except ImportError:
        # Fallback: try json
        _cached_presets = _get_default_presets()
        return _cached_presets

    # Find preset file
    preset_path = DEFAULT_PRESET_PATH

    if not os.path.isabs(preset_path):
        # Try relative to this file
        module_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(module_dir)))
        preset_path = os.path.join(project_root, DEFAULT_PRESET_PATH)

    if os.path.exists(preset_path):
        try:
            with open(preset_path, 'r') as f:
                _cached_presets = yaml.safe_load(f) or {}
                return _cached_presets
        except Exception:
            pass

    # Return defaults if file not found
    _cached_presets = _get_default_presets()
    return _cached_presets


def _get_default_presets() -> Dict[str, Any]:
    """
    Get default presets (embedded).

    Returns:
        Default presets dict
    """
    return {
        "isometric_presets": {
            "classic_pixel": {
                "angle": "pixel",
                "tile_width": 64,
                "tile_height": 32,
                "depth_sorting": True,
            },
            "true_iso": {
                "angle": "true_isometric",
                "tile_width": 64,
                "tile_height": 64,
                "depth_sorting": True,
            },
            "strategy": {
                "angle": "military",
                "tile_width": 64,
                "tile_height": 64,
                "depth_sorting": False,
            },
        },
        "side_scroller_presets": {
            "platformer_16bit": {
                "parallax_layers": 4,
                "layer_depths": [0.1, 0.3, 0.6, 1.0],
                "layer_names": ["sky", "far", "mid", "near"],
            },
            "simple": {
                "parallax_layers": 2,
                "layer_depths": [0.5, 1.0],
                "layer_names": ["background", "foreground"],
            },
        },
        "sprite_sheet_presets": {
            "character": {
                "columns": 8,
                "rows": 4,
                "frame_width": 32,
                "frame_height": 32,
                "trim": True,
                "json_format": "phaser",
            },
            "tileset": {
                "columns": 16,
                "rows": 16,
                "frame_width": 16,
                "frame_height": 16,
                "trim": False,
                "power_of_two": True,
            },
        },
        "tile_presets": {
            "nes": {
                "tile_size": [16, 16],
                "generate_map": True,
                "map_format": "csv",
            },
            "modern_32": {
                "tile_size": [32, 32],
                "generate_map": True,
                "map_format": "tmx",
                "autotile": True,
            },
            "isometric_32": {
                "tile_size": [32, 16],
                "generate_map": True,
                "map_format": "json",
            },
        },
    }


# =============================================================================
# ISOMETRIC PRESETS
# =============================================================================

def load_isometric_preset(name: str) -> Optional[IsometricConfig]:
    """
    Load isometric configuration preset.

    Args:
        name: Preset name

    Returns:
        IsometricConfig or None if not found
    """
    presets = _load_presets_file()
    iso_presets = presets.get("isometric_presets", {})

    if name not in iso_presets:
        return None

    data = iso_presets[name]
    return IsometricConfig.from_dict(data)


def list_isometric_presets() -> List[str]:
    """
    List all available isometric preset names.

    Returns:
        List of preset names
    """
    presets = _load_presets_file()
    return list(presets.get("isometric_presets", {}).keys())


def get_isometric_preset(name: str) -> IsometricConfig:
    """
    Get isometric preset (returns default if not found).

    Args:
        name: Preset name

    Returns:
        IsometricConfig
    """
    config = load_isometric_preset(name)
    if config:
        return config
    return IsometricConfig()


# =============================================================================
# SIDE-SCROLLER PRESETS
# =============================================================================

def load_side_scroller_preset(name: str) -> Optional[SideScrollerConfig]:
    """
    Load side-scroller configuration preset.

    Args:
        name: Preset name

    Returns:
        SideScrollerConfig or None if not found
    """
    presets = _load_presets_file()
    ss_presets = presets.get("side_scroller_presets", {})

    if name not in ss_presets:
        return None

    data = ss_presets[name]
    return SideScrollerConfig.from_dict(data)


def list_side_scroller_presets() -> List[str]:
    """
    List all available side-scroller preset names.

    Returns:
        List of preset names
    """
    presets = _load_presets_file()
    return list(presets.get("side_scroller_presets", {}).keys())


def get_side_scroller_preset(name: str) -> SideScrollerConfig:
    """
    Get side-scroller preset (returns default if not found).

    Args:
        name: Preset name

    Returns:
        SideScrollerConfig
    """
    config = load_side_scroller_preset(name)
    if config:
        return config
    return SideScrollerConfig()


# =============================================================================
# SPRITE SHEET PRESETS
# =============================================================================

def load_sprite_sheet_preset(name: str) -> Optional[SpriteSheetConfig]:
    """
    Load sprite sheet configuration preset.

    Args:
        name: Preset name

    Returns:
        SpriteSheetConfig or None if not found
    """
    presets = _load_presets_file()
    ss_presets = presets.get("sprite_sheet_presets", {})

    if name not in ss_presets:
        return None

    data = ss_presets[name]
    return SpriteSheetConfig.from_dict(data)


def list_sprite_sheet_presets() -> List[str]:
    """
    List all available sprite sheet preset names.

    Returns:
        List of preset names
    """
    presets = _load_presets_file()
    return list(presets.get("sprite_sheet_presets", {}).keys())


def get_sprite_sheet_preset(name: str) -> SpriteSheetConfig:
    """
    Get sprite sheet preset (returns default if not found).

    Args:
        name: Preset name

    Returns:
        SpriteSheetConfig
    """
    config = load_sprite_sheet_preset(name)
    if config:
        return config
    return SpriteSheetConfig()


# =============================================================================
# TILE PRESETS
# =============================================================================

def load_tile_preset(name: str) -> Optional[TileConfig]:
    """
    Load tile configuration preset.

    Args:
        name: Preset name

    Returns:
        TileConfig or None if not found
    """
    presets = _load_presets_file()
    tile_presets = presets.get("tile_presets", {})

    if name not in tile_presets:
        return None

    data = tile_presets[name]
    return TileConfig.from_dict(data)


def list_tile_presets() -> List[str]:
    """
    List all available tile preset names.

    Returns:
        List of preset names
    """
    presets = _load_presets_file()
    return list(presets.get("tile_presets", {}).keys())


def get_tile_preset(name: str) -> TileConfig:
    """
    Get tile preset (returns default if not found).

    Args:
        name: Preset name

    Returns:
        TileConfig
    """
    config = load_tile_preset(name)
    if config:
        return config
    return TileConfig()


# =============================================================================
# GENERIC LOADER
# =============================================================================

def load_view_preset(category: str, name: str) -> Optional[Any]:
    """
    Load a view preset by category and name.

    Args:
        category: Preset category (isometric, side_scroller, sprite_sheet, tile)
        name: Preset name

    Returns:
        Configuration object or None if not found
    """
    if category == "isometric":
        return load_isometric_preset(name)
    elif category == "side_scroller":
        return load_side_scroller_preset(name)
    elif category == "sprite_sheet":
        return load_sprite_sheet_preset(name)
    elif category == "tile":
        return load_tile_preset(name)
    else:
        return None


def list_view_presets(category: Optional[str] = None) -> Dict[str, List[str]]:
    """
    List available view presets.

    Args:
        category: Optional category filter

    Returns:
        Dict mapping categories to preset name lists
    """
    if category:
        if category == "isometric":
            return {"isometric": list_isometric_presets()}
        elif category == "side_scroller":
            return {"side_scroller": list_side_scroller_presets()}
        elif category == "sprite_sheet":
            return {"sprite_sheet": list_sprite_sheet_presets()}
        elif category == "tile":
            return {"tile": list_tile_presets()}
        else:
            return {}

    return {
        "isometric": list_isometric_presets(),
        "side_scroller": list_side_scroller_presets(),
        "sprite_sheet": list_sprite_sheet_presets(),
        "tile": list_tile_presets(),
    }


# =============================================================================
# CACHE MANAGEMENT
# =============================================================================

def clear_preset_cache() -> None:
    """Clear the preset cache."""
    global _cached_presets
    _cached_presets = None


def reload_presets() -> Dict[str, Any]:
    """
    Reload presets from file.

    Returns:
        Reloaded presets dict
    """
    clear_preset_cache()
    return _load_presets_file()
