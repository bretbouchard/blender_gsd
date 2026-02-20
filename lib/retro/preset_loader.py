"""
Preset Loader for Pixel Art Conversion

Loads pixel art profiles from YAML configuration files.
"""

from __future__ import annotations
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from lib.retro.pixel_types import (
    PixelStyle,
    PixelationConfig,
    ColorPalette,
)

# Default search paths for preset files
DEFAULT_SEARCH_PATHS = [
    Path("configs/cinematic/retro/pixel_profiles.yaml"),
    Path("configs/retro/pixel_profiles.yaml"),
    Path("~/.config/blender_gsd/retro/pixel_profiles.yaml"),
]


def load_pixel_profile(
    name: str,
    search_paths: Optional[List[Path]] = None
) -> Optional[PixelationConfig]:
    """
    Load a pixel art profile by name.

    Args:
        name: Profile name (e.g., "snes", "nes", "gameboy")
        search_paths: Optional list of paths to search for config files

    Returns:
        PixelationConfig or None if not found
    """
    config_data = _load_profile_data(name, search_paths)
    if config_data is None:
        return None

    return _parse_profile_config(config_data)


def list_profiles(search_paths: Optional[List[Path]] = None) -> List[str]:
    """
    List all available profile names.

    Args:
        search_paths: Optional list of paths to search for config files

    Returns:
        List of profile names
    """
    data = _load_config_file(search_paths)
    if data is None or "profiles" not in data:
        return []

    return list(data["profiles"].keys())


def load_palette(
    name: str,
    search_paths: Optional[List[Path]] = None
) -> Optional[ColorPalette]:
    """
    Load a color palette by name.

    Args:
        name: Palette name (e.g., "gameboy", "pico8")
        search_paths: Optional list of paths to search for config files

    Returns:
        ColorPalette or None if not found
    """
    data = _load_config_file(search_paths)
    if data is None or "palettes" not in data:
        return None

    palette_data = data["palettes"].get(name)
    if palette_data is None:
        return None

    return _parse_palette(palette_data)


def list_palettes(search_paths: Optional[List[Path]] = None) -> List[str]:
    """
    List all available palette names.

    Args:
        search_paths: Optional list of paths to search for config files

    Returns:
        List of palette names
    """
    data = _load_config_file(search_paths)
    if data is None or "palettes" not in data:
        return []

    return list(data["palettes"].keys())


def load_resolution(
    name: str,
    search_paths: Optional[List[Path]] = None
) -> Optional[Tuple[int, int]]:
    """
    Load a resolution preset by name.

    Args:
        name: Resolution name (e.g., "snes", "pico8", "hd")
        search_paths: Optional list of paths to search for config files

    Returns:
        Tuple of (width, height) or None if not found
    """
    data = _load_config_file(search_paths)
    if data is None or "resolutions" not in data:
        return None

    resolution = data["resolutions"].get(name)
    if resolution is None:
        return None

    return tuple(resolution)


def list_resolutions(search_paths: Optional[List[Path]] = None) -> List[str]:
    """
    List all available resolution preset names.

    Args:
        search_paths: Optional list of paths to search for config files

    Returns:
        List of resolution names
    """
    data = _load_config_file(search_paths)
    if data is None or "resolutions" not in data:
        return []

    return list(data["resolutions"].keys())


def _load_profile_data(
    name: str,
    search_paths: Optional[List[Path]] = None
) -> Optional[Dict[str, Any]]:
    """Load raw profile data from config file."""
    data = _load_config_file(search_paths)
    if data is None or "profiles" not in data:
        return None

    return data["profiles"].get(name)


def _load_config_file(search_paths: Optional[List[Path]] = None) -> Optional[Dict[str, Any]]:
    """Load the config file from search paths."""
    paths = search_paths if search_paths else [Path(p) for p in DEFAULT_SEARCH_PATHS]

    for path in paths:
        expanded = Path(path).expanduser()
        if expanded.exists():
            try:
                return _load_yaml(expanded)
            except Exception:
                continue

    return None


def _load_yaml(path: Path) -> Dict[str, Any]:
    """Load YAML file."""
    try:
        import yaml
        with open(path, "r") as f:
            return yaml.safe_load(f)
    except ImportError:
        # Fallback to simple YAML parsing
        return _parse_yaml_simple(path)


def _parse_yaml_simple(path: Path) -> Dict[str, Any]:
    """
    Simple YAML parser for basic structures.
    Falls back when PyYAML is not available.
    """
    result: Dict[str, Any] = {}
    current_section: Optional[str] = None
    current_item: Optional[str] = None
    indent_stack: List[Tuple[int, str, Any]] = []

    with open(path, "r") as f:
        for line in f:
            stripped = line.lstrip()
            if not stripped or stripped.startswith("#"):
                continue

            indent = len(line) - len(stripped)

            # Handle key: value
            if ":" in stripped:
                key_part, _, value_part = stripped.partition(":")
                key = key_part.strip()
                value = value_part.strip()

                if value:
                    # Simple key: value
                    parsed_value = _parse_yaml_value(value)
                    if indent_stack:
                        # Find correct parent
                        while indent_stack and indent_stack[-1][0] >= indent:
                            indent_stack.pop()
                        if indent_stack:
                            parent_dict = indent_stack[-1][2]
                            parent_dict[key] = parsed_value
                        else:
                            result[key] = parsed_value
                    else:
                        result[key] = parsed_value
                else:
                    # Section start
                    if indent == 0:
                        current_section = key
                        result[current_section] = {}
                        indent_stack = [(0, current_section, result[current_section])]
                    else:
                        # Sub-section
                        while indent_stack and indent_stack[-1][0] >= indent:
                            indent_stack.pop()

                        if indent_stack:
                            parent_dict = indent_stack[-1][2]
                            parent_dict[key] = {}
                            indent_stack.append((indent, key, parent_dict[key]))

    return result


def _parse_yaml_value(value: str) -> Any:
    """Parse a YAML value string."""
    value = value.strip()

    # Remove quotes
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]

    # Boolean
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    # Integer
    try:
        return int(value)
    except ValueError:
        pass

    # Float
    try:
        return float(value)
    except ValueError:
        pass

    # List
    if value.startswith("[") and value.endswith("]"):
        items = value[1:-1].split(",")
        return [_parse_yaml_value(item.strip()) for item in items if item.strip()]

    return value


def _parse_profile_config(data: Dict[str, Any]) -> PixelationConfig:
    """Parse profile data into PixelationConfig."""
    style_data = data.get("style", {})
    style = PixelStyle(
        mode=style_data.get("mode", "16bit"),
        pixel_size=style_data.get("pixel_size", 1),
        color_limit=style_data.get("color_limit", 256),
        preserve_edges=style_data.get("preserve_edges", True),
        posterize_levels=style_data.get("posterize_levels", 0),
        sub_pixel_layout=style_data.get("sub_pixel_layout", "none"),
        dither_mode=style_data.get("dither_mode", "none"),
        dither_strength=style_data.get("dither_strength", 1.0),
    )

    target_res = data.get("target_resolution", [0, 0])
    if isinstance(target_res, list):
        target_res = tuple(target_res)

    return PixelationConfig(
        style=style,
        target_resolution=target_res,
        aspect_ratio_mode=data.get("aspect_ratio_mode", "preserve"),
        scaling_filter=data.get("scaling_filter", "nearest"),
        edge_detection=data.get("edge_detection", True),
        edge_threshold=data.get("edge_threshold", 0.1),
        edge_enhancement=data.get("edge_enhancement", 0.0),
        output_scale=data.get("output_scale", 1),
        palette_name=data.get("palette_name", ""),
    )


def _parse_palette(data: Dict[str, Any]) -> ColorPalette:
    """Parse palette data into ColorPalette."""
    colors_data = data.get("colors", [])
    colors = [tuple(c) for c in colors_data]

    return ColorPalette(
        name=data.get("name", ""),
        colors=colors,
        description=data.get("description", ""),
        source=data.get("source", ""),
    )


# Convenience functions for common profiles

def get_snes_config() -> PixelationConfig:
    """Get SNES-style configuration."""
    config = load_pixel_profile("snes")
    if config:
        return config
    return PixelationConfig.for_console("snes")


def get_nes_config() -> PixelationConfig:
    """Get NES-style configuration."""
    config = load_pixel_profile("nes")
    if config:
        return config
    return PixelationConfig.for_console("nes")


def get_gameboy_config() -> PixelationConfig:
    """Get Game Boy-style configuration."""
    config = load_pixel_profile("gameboy")
    if config:
        return config
    return PixelationConfig.for_console("gameboy")


def get_pico8_config() -> PixelationConfig:
    """Get PICO-8-style configuration."""
    config = load_pixel_profile("pico8")
    if config:
        return config
    return PixelationConfig.for_console("pico8")
