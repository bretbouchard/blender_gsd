"""
IK Presets Module

Loading and saving IK configuration presets.

Phase 13.1: IK/FK System (REQ-ANIM-02)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import json

from .types import IKConfig, IKMode, SplineIKConfig, IKFKBlendConfig

# Configuration root directory
IK_CONFIG_ROOT = Path(__file__).parent.parent.parent / "configs" / "animation" / "ik"

# Cache for loaded presets
_ik_preset_cache: Dict[str, IKConfig] = {}
_spline_ik_cache: Dict[str, SplineIKConfig] = {}
_blend_cache: Dict[str, IKFKBlendConfig] = {}


def _try_yaml_load(data: str) -> Dict[str, Any]:
    """Try to load YAML, fall back to JSON."""
    try:
        import yaml
        return yaml.safe_load(data)
    except ImportError:
        # Fall back to JSON (YAML is JSON-compatible for simple cases)
        return json.loads(data)


def _try_yaml_dump(data: Dict[str, Any]) -> str:
    """Try to dump as YAML, fall back to JSON."""
    try:
        import yaml
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
    except ImportError:
        return json.dumps(data, indent=2)


def list_ik_presets() -> List[str]:
    """
    List available IK presets.

    Returns:
        List of preset names (without .yaml extension)
    """
    if not IK_CONFIG_ROOT.exists():
        return []

    presets = []
    for yaml_file in IK_CONFIG_ROOT.glob("*.yaml"):
        presets.append(yaml_file.stem)

    return sorted(presets)


def ik_preset_exists(preset_id: str) -> bool:
    """
    Check if an IK preset exists.

    Args:
        preset_id: Preset identifier

    Returns:
        True if preset exists
    """
    preset_path = IK_CONFIG_ROOT / f"{preset_id}.yaml"
    return preset_path.exists()


def load_ik_preset(
    preset_id: str,
    use_cache: bool = True
) -> IKConfig:
    """
    Load an IK preset configuration.

    Args:
        preset_id: Preset identifier
        use_cache: Use cached version if available

    Returns:
        IKConfig object

    Raises:
        FileNotFoundError: If preset doesn't exist
    """
    if use_cache and preset_id in _ik_preset_cache:
        return _ik_preset_cache[preset_id]

    preset_path = IK_CONFIG_ROOT / f"{preset_id}.yaml"

    if not preset_path.exists():
        raise FileNotFoundError(f"IK preset not found: {preset_id}")

    with open(preset_path) as f:
        data = _try_yaml_load(f.read())

    config = _parse_ik_config(data)

    if use_cache:
        _ik_preset_cache[preset_id] = config

    return config


def load_spline_ik_preset(
    preset_id: str,
    use_cache: bool = True
) -> SplineIKConfig:
    """
    Load a spline IK preset configuration.

    Args:
        preset_id: Preset identifier
        use_cache: Use cached version if available

    Returns:
        SplineIKConfig object

    Raises:
        FileNotFoundError: If preset doesn't exist
    """
    if use_cache and preset_id in _spline_ik_cache:
        return _spline_ik_cache[preset_id]

    preset_path = IK_CONFIG_ROOT / "spline" / f"{preset_id}.yaml"

    if not preset_path.exists():
        raise FileNotFoundError(f"Spline IK preset not found: {preset_id}")

    with open(preset_path) as f:
        data = _try_yaml_load(f.read())

    config = SplineIKConfig.from_dict(data)

    if use_cache:
        _spline_ik_cache[preset_id] = config

    return config


def load_blend_preset(
    preset_id: str,
    use_cache: bool = True
) -> IKFKBlendConfig:
    """
    Load an IK/FK blend preset configuration.

    Args:
        preset_id: Preset identifier
        use_cache: Use cached version if available

    Returns:
        IKFKBlendConfig object

    Raises:
        FileNotFoundError: If preset doesn't exist
    """
    if use_cache and preset_id in _blend_cache:
        return _blend_cache[preset_id]

    preset_path = IK_CONFIG_ROOT / "blend" / f"{preset_id}.yaml"

    if not preset_path.exists():
        raise FileNotFoundError(f"Blend preset not found: {preset_id}")

    with open(preset_path) as f:
        data = _try_yaml_load(f.read())

    config = IKFKBlendConfig.from_dict(data)

    if use_cache:
        _blend_cache[preset_id] = config

    return config


def save_ik_config(
    config: IKConfig,
    preset_id: str,
    overwrite: bool = False
) -> Path:
    """
    Save IK configuration as a preset.

    Args:
        config: IKConfig to save
        preset_id: Preset identifier
        overwrite: Overwrite existing preset

    Returns:
        Path to saved preset file

    Raises:
        FileExistsError: If preset exists and overwrite is False
    """
    IK_CONFIG_ROOT.mkdir(parents=True, exist_ok=True)

    preset_path = IK_CONFIG_ROOT / f"{preset_id}.yaml"

    if preset_path.exists() and not overwrite:
        raise FileExistsError(f"Preset already exists: {preset_id}")

    data = config.to_dict()
    yaml_content = _try_yaml_dump(data)

    with open(preset_path, 'w') as f:
        f.write(yaml_content)

    # Update cache
    _ik_preset_cache[preset_id] = config

    return preset_path


def _parse_ik_config(data: Dict[str, Any]) -> IKConfig:
    """Parse IKConfig from dictionary."""
    return IKConfig(
        name=data.get('name', ''),
        chain=data.get('chain', []),
        target=data.get('target'),
        pole_target=data.get('pole_target'),
        pole_angle=data.get('pole_angle', 0.0),
        chain_count=data.get('chain_count', 2),
        iterations=data.get('iterations', 500),
        mode=IKMode(data.get('mode', 'two_bone')),
        use_tail=data.get('use_tail', False),
        stretch=data.get('stretch', 0.0),
        weight=data.get('weight', 1.0),
        lock_rotation=data.get('lock_rotation', False),
    )


def clear_cache() -> None:
    """Clear all preset caches."""
    global _ik_preset_cache, _spline_ik_cache, _blend_cache
    _ik_preset_cache = {}
    _spline_ik_cache = {}
    _blend_cache = {}


def get_preset_path(preset_id: str) -> Path:
    """
    Get path to preset file.

    Args:
        preset_id: Preset identifier

    Returns:
        Path to preset file
    """
    return IK_CONFIG_ROOT / f"{preset_id}.yaml"


def load_limb_ik_presets() -> Dict[str, IKConfig]:
    """
    Load all limb IK presets.

    Returns:
        Dictionary of preset name to IKConfig
    """
    limb_presets = {}

    # Try to load from limb_ik.yaml which contains multiple presets
    limb_ik_path = IK_CONFIG_ROOT / "limb_ik.yaml"

    if limb_ik_path.exists():
        with open(limb_ik_path) as f:
            data = _try_yaml_load(f.read())

        # Check if it's a multi-preset file
        if 'presets' in data:
            for name, preset_data in data['presets'].items():
                limb_presets[name] = _parse_ik_config(preset_data)
        else:
            # Single preset file
            limb_presets['default'] = _parse_ik_config(data)

    return limb_presets


def load_chain_ik_presets() -> Dict[str, IKConfig]:
    """
    Load all chain IK presets.

    Returns:
        Dictionary of preset name to IKConfig
    """
    chain_presets = {}

    chain_ik_path = IK_CONFIG_ROOT / "chain_ik.yaml"

    if chain_ik_path.exists():
        with open(chain_ik_path) as f:
            data = _try_yaml_load(f.read())

        if 'presets' in data:
            for name, preset_data in data['presets'].items():
                chain_presets[name] = _parse_ik_config(preset_data)
        else:
            chain_presets['default'] = _parse_ik_config(data)

    return chain_presets


# Convenience exports
__all__ = [
    'list_ik_presets',
    'ik_preset_exists',
    'load_ik_preset',
    'load_spline_ik_preset',
    'load_blend_preset',
    'save_ik_config',
    'clear_cache',
    'get_preset_path',
    'load_limb_ik_presets',
    'load_chain_ik_presets',
]
