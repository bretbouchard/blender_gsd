"""
Tentacle Material Presets

YAML preset loading system for tentacle materials with caching.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

import yaml

from .types import (
    MaterialTheme,
    WetnessLevel,
    SSSConfig,
    WetnessConfig,
    VeinConfig,
    RoughnessConfig,
    MaterialZone,
    ThemePreset,
    TentacleMaterialConfig,
    BakeConfig,
)


# Cache for loaded presets
_preset_cache: Dict[str, Any] = {}


def _get_preset_path() -> Path:
    """Get path to presets directory."""
    # Look for presets relative to this file
    module_dir = Path(__file__).parent
    project_root = module_dir.parent.parent.parent
    return project_root / "configs" / "tentacle"


def _load_yaml(filename: str, use_cache: bool = True) -> Dict[str, Any]:
    """
    Load YAML file with optional caching.

    Args:
        filename: YAML filename (without path)
        use_cache: Whether to use cached data

    Returns:
        Parsed YAML data as dictionary
    """
    if use_cache and filename in _preset_cache:
        return _preset_cache[filename]

    filepath = _get_preset_path() / filename
    if not filepath.exists():
        return {}

    with open(filepath, "r") as f:
        data = yaml.safe_load(f) or {}

    if use_cache:
        _preset_cache[filename] = data

    return data


def _parse_sss_config(data: Dict[str, Any]) -> SSSConfig:
    """Parse SSS config from YAML data."""
    return SSSConfig(
        radius=data.get("radius", 1.0),
        color=tuple(data.get("color", [1.0, 0.2, 0.2])),
        weight=data.get("weight", 1.0),
        anisotropy=data.get("anisotropy", 0.0),
        ior=data.get("ior", 1.4),
    )


def _parse_wetness_config(data: Dict[str, Any]) -> WetnessConfig:
    """Parse wetness config from YAML data."""
    level_str = data.get("level", "dry")
    level = WetnessLevel(level_str) if level_str in [e.value for e in WetnessLevel] else WetnessLevel.DRY

    return WetnessConfig(
        level=level,
        intensity=data.get("intensity", 0.5),
        roughness_modifier=data.get("roughness_modifier", 0.3),
        specular_boost=data.get("specular_boost", 0.5),
        clearcoat=data.get("clearcoat", 0.0),
    )


def _parse_vein_config(data: Dict[str, Any]) -> VeinConfig:
    """Parse vein config from YAML data."""
    return VeinConfig(
        enabled=data.get("enabled", True),
        color=tuple(data.get("color", [0.3, 0.0, 0.0])),
        density=data.get("density", 0.5),
        scale=data.get("scale", 0.1),
        depth=data.get("depth", 0.02),
        glow=data.get("glow", False),
        glow_color=tuple(data.get("glow_color", [0.0, 1.0, 0.5])),
        glow_intensity=data.get("glow_intensity", 0.5),
    )


def _parse_roughness_config(data: Dict[str, Any]) -> RoughnessConfig:
    """Parse roughness config from YAML data."""
    return RoughnessConfig(
        base=data.get("base", 0.5),
        variation=data.get("variation", 0.1),
        metallic=data.get("metallic", 0.0),
        normal_strength=data.get("normal_strength", 0.5),
    )


def _parse_material_zone(data: Dict[str, Any]) -> MaterialZone:
    """Parse material zone from YAML data."""
    return MaterialZone(
        name=data.get("name", "zone"),
        position=data.get("position", 0.5),
        width=data.get("width", 0.33),
        color_tint=tuple(data.get("color_tint", [1.0, 1.0, 1.0])),
        roughness_offset=data.get("roughness_offset", 0.0),
        sss_offset=data.get("sss_offset", 0.0),
    )


def _parse_theme_preset(name: str, data: Dict[str, Any]) -> ThemePreset:
    """Parse theme preset from YAML data."""
    theme_str = data.get("theme", name.lower())
    theme = MaterialTheme(theme_str) if theme_str in [e.value for e in MaterialTheme] else MaterialTheme.ROTTING

    return ThemePreset(
        name=data.get("name", name),
        theme=theme,
        description=data.get("description", ""),
        base_color=tuple(data.get("base_color", [0.5, 0.4, 0.35])),
        sss=_parse_sss_config(data.get("sss", {})),
        wetness=_parse_wetness_config(data.get("wetness", {})),
        veins=_parse_vein_config(data.get("veins", {})),
        roughness=_parse_roughness_config(data.get("roughness", {})),
        emission_color=tuple(data.get("emission_color", [0.0, 0.0, 0.0])),
        emission_strength=data.get("emission_strength", 0.0),
    )


def _parse_material_config(data: Dict[str, Any]) -> TentacleMaterialConfig:
    """Parse full material config from YAML data."""
    theme_preset = None
    if "theme_preset" in data:
        theme_preset = _parse_theme_preset("custom", data["theme_preset"])

    zones = []
    for zone_data in data.get("zones", []):
        zones.append(_parse_material_zone(zone_data))

    return TentacleMaterialConfig(
        name=data.get("name", "TentacleMaterial"),
        theme_preset=theme_preset,
        zones=zones,
        blend_zones=data.get("blend_zones", True),
        global_wetness_multiplier=data.get("global_wetness_multiplier", 1.0),
        global_sss_multiplier=data.get("global_sss_multiplier", 1.0),
        noise_scale=data.get("noise_scale", 1.0),
        noise_detail=data.get("noise_detail", 4),
        seed=data.get("seed"),
    )


def _parse_bake_config(data: Dict[str, Any]) -> BakeConfig:
    """Parse bake config from YAML data."""
    return BakeConfig(
        resolution=data.get("resolution", 2048),
        bake_albedo=data.get("bake_albedo", True),
        bake_normal=data.get("bake_normal", True),
        bake_roughness=data.get("bake_roughness", True),
        bake_sss=data.get("bake_sss", True),
        bake_emission=data.get("bake_emission", False),
        output_format=data.get("output_format", "PNG"),
        output_directory=data.get("output_directory"),
        denoise=data.get("denoise", True),
        samples=data.get("samples", 64),
    )


def load_theme_preset(name: str, use_cache: bool = True) -> Optional[ThemePreset]:
    """
    Load a theme preset from YAML.

    Args:
        name: Theme preset name (rotting, parasitic, demonic, mutated, decayed)
        use_cache: Whether to use cached data

    Returns:
        ThemePreset or None if not found
    """
    data = _load_yaml("material_presets.yaml", use_cache)
    themes = data.get("themes", {})

    # Try exact match first
    if name in themes:
        return _parse_theme_preset(name, themes[name])

    # Try lowercase match
    name_lower = name.lower()
    if name_lower in themes:
        return _parse_theme_preset(name_lower, themes[name_lower])

    # Try enum value match
    for theme_name, theme_data in themes.items():
        if theme_name.lower() == name_lower:
            return _parse_theme_preset(theme_name, theme_data)

    return None


def load_material_config(name: str, use_cache: bool = True) -> Optional[TentacleMaterialConfig]:
    """
    Load a material configuration from YAML.

    Args:
        name: Material config name
        use_cache: Whether to use cached data

    Returns:
        TentacleMaterialConfig or None if not found
    """
    data = _load_yaml("material_presets.yaml", use_cache)
    configs = data.get("materials", {})

    if name not in configs:
        return None

    return _parse_material_config(configs[name])


def load_bake_config(name: str = "default", use_cache: bool = True) -> BakeConfig:
    """
    Load a bake configuration from YAML.

    Args:
        name: Bake config name (default is "default")
        use_cache: Whether to use cached data

    Returns:
        BakeConfig (defaults if not found)
    """
    data = _load_yaml("material_presets.yaml", use_cache)
    configs = data.get("baking", {})

    if name in configs:
        return _parse_bake_config(configs[name])

    return BakeConfig()


def list_theme_presets(use_cache: bool = True) -> List[str]:
    """
    List available theme presets.

    Args:
        use_cache: Whether to use cached data

    Returns:
        List of theme preset names
    """
    data = _load_yaml("material_presets.yaml", use_cache)
    return list(data.get("themes", {}).keys())


def list_material_configs(use_cache: bool = True) -> List[str]:
    """
    List available material configurations.

    Args:
        use_cache: Whether to use cached data

    Returns:
        List of material config names
    """
    data = _load_yaml("material_presets.yaml", use_cache)
    return list(data.get("materials", {}).keys())


def clear_cache() -> None:
    """Clear the preset cache."""
    global _preset_cache
    _preset_cache = {}


class MaterialPresetLoader:
    """
    Material preset loader with caching and custom paths.

    Provides a higher-level interface for loading and managing
    tentacle material presets.
    """

    def __init__(
        self,
        preset_path: Optional[Path] = None,
        cache_enabled: bool = True,
    ):
        """
        Initialize preset loader.

        Args:
            preset_path: Custom path to presets directory
            cache_enabled: Whether to cache loaded presets
        """
        self._preset_path = preset_path or _get_preset_path()
        self._cache_enabled = cache_enabled
        self._local_cache: Dict[str, Any] = {}

    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load YAML file using instance settings."""
        if self._cache_enabled and filename in self._local_cache:
            return self._local_cache[filename]

        filepath = self._preset_path / filename
        if not filepath.exists():
            return {}

        with open(filepath, "r") as f:
            data = yaml.safe_load(f) or {}

        if self._cache_enabled:
            self._local_cache[filename] = data

        return data

    def load_theme(self, name: str) -> Optional[ThemePreset]:
        """Load a theme preset."""
        data = self._load_yaml("material_presets.yaml")
        themes = data.get("themes", {})

        name_lower = name.lower()
        for theme_name, theme_data in themes.items():
            if theme_name.lower() == name_lower:
                return _parse_theme_preset(theme_name, theme_data)

        return None

    def load_material(self, name: str) -> Optional[TentacleMaterialConfig]:
        """Load a material configuration."""
        data = self._load_yaml("material_presets.yaml")
        configs = data.get("materials", {})

        if name not in configs:
            return None

        return _parse_material_config(configs[name])

    def load_bake_config(self, name: str = "default") -> BakeConfig:
        """Load a bake configuration."""
        data = self._load_yaml("material_presets.yaml")
        configs = data.get("baking", {})

        if name in configs:
            return _parse_bake_config(configs[name])

        return BakeConfig()

    def list_themes(self) -> List[str]:
        """List available theme presets."""
        data = self._load_yaml("material_presets.yaml")
        return list(data.get("themes", {}).keys())

    def list_materials(self) -> List[str]:
        """List available material configurations."""
        data = self._load_yaml("material_presets.yaml")
        return list(data.get("materials", {}).keys())

    def clear_cache(self) -> None:
        """Clear the local cache."""
        self._local_cache.clear()

    def reload(self) -> None:
        """Reload all presets from disk."""
        self.clear_cache()
