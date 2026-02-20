"""
CRT Preset Loader Module

Loads CRT effect presets from YAML configuration files.
Extends the built-in presets with YAML-based presets.

Example Usage:
    from lib.retro.crt_preset_loader import load_crt_preset, list_crt_presets

    config = load_crt_preset("arcade_80s")
    result = apply_all_effects(image, config)
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import os

from lib.retro.crt_types import (
    CRTConfig,
    ScanlineConfig,
    PhosphorConfig,
    CurvatureConfig,
    CRT_PRESETS,
    get_preset as get_builtin_preset,
    list_presets as list_builtin_presets,
)


# Default search paths for CRT preset files
CRT_PRESET_PATHS = [
    Path("configs/cinematic/retro/crt_presets.yaml"),
    Path("configs/retro/crt_presets.yaml"),
    Path("crt_presets.yaml"),
]

# Cache for loaded presets
_preset_cache: Dict[str, CRTConfig] = {}
_yaml_presets_loaded = False


def _find_preset_file() -> Optional[Path]:
    """Find the CRT preset YAML file."""
    # Check current directory first
    for path in CRT_PRESET_PATHS:
        if path.exists():
            return path

    # Check relative to module location
    module_dir = Path(__file__).parent.parent.parent
    for rel_path in CRT_PRESET_PATHS:
        full_path = module_dir / rel_path
        if full_path.exists():
            return full_path

    return None


def _load_yaml_presets() -> Dict[str, Dict[str, Any]]:
    """Load presets from YAML file."""
    global _yaml_presets_loaded

    presets = {}

    preset_file = _find_preset_file()
    if preset_file is None:
        _yaml_presets_loaded = True
        return presets

    try:
        import yaml
        with open(preset_file, 'r') as f:
            data = yaml.safe_load(f)

        if data and 'presets' in data:
            presets = data['presets']

        _yaml_presets_loaded = True
    except ImportError:
        # PyYAML not available
        _yaml_presets_loaded = True
    except Exception as e:
        print(f"Warning: Could not load CRT presets: {e}")
        _yaml_presets_loaded = True

    return presets


def _parse_preset_config(data: Dict[str, Any]) -> CRTConfig:
    """Parse a preset dictionary into CRTConfig."""
    # Parse scanlines
    scanlines_data = data.get('scanlines', {})
    scanlines = ScanlineConfig(
        enabled=scanlines_data.get('enabled', True),
        intensity=scanlines_data.get('intensity', 0.3),
        spacing=scanlines_data.get('spacing', 2),
        thickness=scanlines_data.get('thickness', 0.5),
        mode=scanlines_data.get('mode', 'alternate'),
        brightness_compensation=scanlines_data.get('brightness_compensation', 1.1),
    )

    # Parse phosphor
    phosphor_data = data.get('phosphor', {})
    phosphor = PhosphorConfig(
        enabled=phosphor_data.get('enabled', False),
        pattern=phosphor_data.get('pattern', 'rgb'),
        intensity=phosphor_data.get('intensity', 0.5),
        scale=phosphor_data.get('scale', 1.0),
        slot_width=phosphor_data.get('slot_width', 2),
        slot_height=phosphor_data.get('slot_height', 4),
    )

    # Parse curvature
    curvature_data = data.get('curvature', {})
    if isinstance(curvature_data, dict):
        curvature = CurvatureConfig(
            enabled=curvature_data.get('enabled', False),
            amount=curvature_data.get('amount', 0.1),
            vignette_amount=curvature_data.get('vignette_amount', 0.2),
            corner_radius=curvature_data.get('corner_radius', 0),
            border_size=curvature_data.get('border_size', 0),
        )
    else:
        curvature = CurvatureConfig(enabled=False)

    # Create CRTConfig
    config = CRTConfig(
        name=data.get('name', 'custom'),
        scanlines=scanlines,
        phosphor=phosphor,
        curvature=curvature,
        bloom=data.get('bloom', 0.0),
        chromatic_aberration=data.get('chromatic_aberration', 0.0),
        flicker=data.get('flicker', 0.0),
        interlace=data.get('interlace', False),
        pixel_jitter=data.get('pixel_jitter', 0.0),
        noise=data.get('noise', 0.0),
        ghosting=data.get('ghosting', 0.0),
        brightness=data.get('brightness', 1.0),
        contrast=data.get('contrast', 1.0),
        saturation=data.get('saturation', 1.0),
        gamma=data.get('gamma', 2.2),
    )

    return config


def load_crt_preset(name: str) -> CRTConfig:
    """
    Load a CRT preset by name.

    Checks built-in presets first, then YAML presets.

    Args:
        name: Preset name

    Returns:
        CRTConfig for the preset

    Raises:
        KeyError: If preset not found
    """
    # Check cache
    if name in _preset_cache:
        return _preset_cache[name]

    # Check built-in presets
    try:
        return get_builtin_preset(name)
    except KeyError:
        pass

    # Load YAML presets
    yaml_presets = _load_yaml_presets()

    if name in yaml_presets:
        config = _parse_preset_config(yaml_presets[name])
        config.name = name  # Ensure name matches
        _preset_cache[name] = config
        return config

    raise KeyError(f"CRT preset '{name}' not found. Available: {list_crt_presets()}")


def list_crt_presets() -> List[str]:
    """
    List all available CRT presets.

    Combines built-in and YAML presets.

    Returns:
        List of preset names
    """
    presets = set(list_builtin_presets())

    yaml_presets = _load_yaml_presets()
    presets.update(yaml_presets.keys())

    return sorted(presets)


def get_crt_preset(name: str) -> CRTConfig:
    """
    Alias for load_crt_preset.

    Args:
        name: Preset name

    Returns:
        CRTConfig for the preset
    """
    return load_crt_preset(name)


def get_crt_preset_description(name: str) -> str:
    """
    Get description for a CRT preset.

    Args:
        name: Preset name

    Returns:
        Human-readable description
    """
    # Check YAML presets for description
    yaml_presets = _load_yaml_presets()
    if name in yaml_presets:
        return yaml_presets[name].get('description', 'No description available')

    # Fall back to built-in description
    from lib.retro.crt_types import get_preset_description
    return get_preset_description(name)


def clear_preset_cache() -> None:
    """Clear the preset cache."""
    global _preset_cache, _yaml_presets_loaded
    _preset_cache = {}
    _yaml_presets_loaded = False


def reload_presets() -> None:
    """Reload presets from YAML file."""
    clear_preset_cache()


# Convenience functions matching the existing pattern
def get_arcade_80s() -> CRTConfig:
    """Get arcade 80s preset."""
    return load_crt_preset("arcade_80s")


def get_crt_tv() -> CRTConfig:
    """Get CRT TV preset."""
    return load_crt_preset("crt_tv_90s")


def get_pvm() -> CRTConfig:
    """Get Sony PVM preset."""
    return load_crt_preset("sony_pvm")


def get_gameboy() -> CRTConfig:
    """Get Game Boy LCD preset."""
    return load_crt_preset("gameboy_lcd")
