"""
Rig Preset Loader

Load and save rig configurations from YAML files.

Phase 13.0: Rigging Foundation (REQ-ANIM-01)
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

from .types import (
    RigConfig,
    BoneConfig,
    BoneConstraint,
    BoneGroupConfig,
    IKChain,
    RigType,
)


# Configuration root directory
RIG_CONFIG_ROOT = Path(__file__).parent.parent.parent / "configs" / "animation" / "rigs"

# Cache for loaded presets
_rig_cache: Dict[str, RigConfig] = {}


def load_rig_preset(preset_id: str, use_cache: bool = True) -> RigConfig:
    """
    Load a rig preset from YAML file.

    Args:
        preset_id: The preset identifier (filename without .yaml)
        use_cache: Whether to use cached presets

    Returns:
        RigConfig object

    Raises:
        FileNotFoundError: If preset file doesn't exist
        ValueError: If preset file is invalid
    """
    if use_cache and preset_id in _rig_cache:
        return _rig_cache[preset_id]

    preset_path = RIG_CONFIG_ROOT / f"{preset_id}.yaml"

    if not preset_path.exists():
        raise FileNotFoundError(f"Rig preset not found: {preset_id}")

    # Try YAML first, fall back to JSON
    data = _load_config_file(preset_path)

    config = _parse_rig_config(data)

    if use_cache:
        _rig_cache[preset_id] = config

    return config


def _load_config_file(path: Path) -> Dict[str, Any]:
    """Load configuration from YAML or JSON file."""
    try:
        import yaml
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        # Fallback to JSON
        json_path = path.with_suffix('.json')
        if json_path.exists():
            with open(json_path, 'r') as f:
                return json.load(f)
        else:
            # Manual YAML-like parsing for simple cases
            with open(path, 'r') as f:
                content = f.read()
            return _parse_simple_yaml(content)


def _parse_simple_yaml(content: str) -> Dict[str, Any]:
    """Simple YAML parser for basic configs without PyYAML."""
    # This is a very basic parser - use PyYAML for complex configs
    import re

    result: Dict[str, Any] = {}
    lines = content.split('\n')

    for line in lines:
        # Skip comments and empty lines
        if not line.strip() or line.strip().startswith('#'):
            continue

        # Match key: value patterns at root level
        match = re.match(r'^(\w+):\s*(.*)$', line)
        if match:
            key = match.group(1)
            value = match.group(2).strip()

            # Try to parse value
            if value.startswith('"') and value.endswith('"'):
                result[key] = value[1:-1]
            elif value.startswith('[') and value.endswith(']'):
                # Simple list
                items = value[1:-1].split(',')
                result[key] = [item.strip().strip('"') for item in items if item.strip()]
            elif value.isdigit():
                result[key] = int(value)
            elif re.match(r'^-?\d+\.?\d*$', value):
                result[key] = float(value)
            else:
                result[key] = value

    return result


def _parse_rig_config(data: Dict[str, Any]) -> RigConfig:
    """Parse dictionary data into RigConfig."""
    # Parse bones
    bones = []
    for bone_data in data.get('bones', []):
        bones.append(_parse_bone(bone_data))

    # Parse constraints
    constraints = []
    for constraint_data in data.get('constraints', []):
        constraints.append(_parse_constraint(constraint_data))

    # Parse groups
    groups = []
    for group_data in data.get('groups', []):
        groups.append(_parse_group(group_data))

    # Parse IK chains
    ik_chains = []
    for ik_data in data.get('ik_chains', []):
        ik_chains.append(_parse_ik_chain(ik_data))

    # Parse rig type
    try:
        rig_type = RigType(data.get('rig_type', 'custom'))
    except ValueError:
        rig_type = RigType.CUSTOM

    return RigConfig(
        id=data['id'],
        name=data['name'],
        version=data.get('version', '1.0'),
        rig_type=rig_type,
        description=data.get('description', ''),
        bones=bones,
        constraints=constraints,
        groups=groups,
        ik_chains=ik_chains,
        custom_properties=data.get('custom_properties', {}),
        metadata=data.get('metadata', {}),
    )


def _parse_bone(data: Dict[str, Any]) -> BoneConfig:
    """Parse bone configuration."""
    return BoneConfig(
        id=data['id'],
        parent=data.get('parent'),
        head=tuple(data['head']) if isinstance(data['head'], list) else data['head'],
        tail=tuple(data['tail']) if isinstance(data['tail'], list) else data['tail'],
        roll=data.get('roll', 0.0),
        layers=data.get('layers', [0]),
        mirror=data.get('mirror'),
        use_connect=data.get('use_connect', False),
        use_inherit_rotation=data.get('use_inherit_rotation', True),
        use_local_location=data.get('use_local_location', True),
        use_deform=data.get('use_deform', True),
        head_radius=data.get('head_radius', 0.1),
        tail_radius=data.get('tail_radius', 0.05),
        hide=data.get('hide', False),
    )


def _parse_constraint(data: Dict[str, Any]) -> BoneConstraint:
    """Parse constraint configuration."""
    return BoneConstraint(
        bone=data['bone'],
        type=data['type'],
        target=data.get('target'),
        subtarget=data.get('subtarget'),
        influence=data.get('influence', 1.0),
        properties=data.get('properties', {}),
    )


def _parse_group(data: Dict[str, Any]) -> BoneGroupConfig:
    """Parse bone group configuration."""
    return BoneGroupConfig(
        name=data['name'],
        bones=data['bones'],
        color=data.get('color', 'DEFAULT'),
        color_set=data.get('color_set', 'DEFAULT'),
    )


def _parse_ik_chain(data: Dict[str, Any]) -> IKChain:
    """Parse IK chain configuration."""
    return IKChain(
        name=data['name'],
        chain=data['chain'],
        target=data.get('target'),
        pole_target=data.get('pole_target'),
        pole_angle=data.get('pole_angle', 0.0),
        iterations=data.get('iterations', 500),
        chain_count=data.get('chain_count', 2),
        use_tail=data.get('use_tail', False),
        use_stretch=data.get('use_stretch', False),
    )


def list_available_presets() -> List[str]:
    """
    List all available rig presets.

    Returns:
        List of preset IDs
    """
    if not RIG_CONFIG_ROOT.exists():
        return []

    presets = []
    for ext in ['*.yaml', '*.yml', '*.json']:
        for f in RIG_CONFIG_ROOT.glob(ext):
            presets.append(f.stem)

    return sorted(set(presets))


def save_rig_config(config: RigConfig, path: Optional[Path] = None) -> Path:
    """
    Save a rig configuration to YAML file.

    Args:
        config: RigConfig to save
        path: Optional path (defaults to configs/animation/rigs/{id}.yaml)

    Returns:
        Path to saved file
    """
    save_path = path or (RIG_CONFIG_ROOT / f"{config.id}.yaml")

    # Ensure directory exists
    save_path.parent.mkdir(parents=True, exist_ok=True)

    # Build data structure
    data = {
        'id': config.id,
        'name': config.name,
        'version': config.version,
        'rig_type': config.rig_type.value,
        'description': config.description,
        'bones': [b.to_dict() for b in config.bones],
        'groups': [g.to_dict() for g in config.groups],
        'ik_chains': [i.to_dict() for i in config.ik_chains],
        'custom_properties': config.custom_properties,
        'metadata': config.metadata,
    }

    # Add constraints if present
    if config.constraints:
        data['constraints'] = [c.to_dict() for c in config.constraints]

    # Try YAML, fall back to JSON
    try:
        import yaml
        with open(save_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    except ImportError:
        # Fallback to JSON
        json_path = save_path.with_suffix('.json')
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
        return json_path

    return save_path


def clear_cache() -> None:
    """Clear the preset cache."""
    global _rig_cache
    _rig_cache = {}


def get_preset_path(preset_id: str) -> Optional[Path]:
    """Get the file path for a preset."""
    for ext in ['.yaml', '.yml', '.json']:
        path = RIG_CONFIG_ROOT / f"{preset_id}{ext}"
        if path.exists():
            return path
    return None


def preset_exists(preset_id: str) -> bool:
    """Check if a preset exists."""
    return get_preset_path(preset_id) is not None


def validate_preset(preset_id: str) -> List[str]:
    """
    Validate a preset configuration.

    Args:
        preset_id: The preset to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    try:
        config = load_rig_preset(preset_id, use_cache=False)
    except FileNotFoundError:
        return [f"Preset '{preset_id}' not found"]
    except Exception as e:
        return [f"Failed to load preset: {e}"]

    # Check for required fields
    if not config.id:
        errors.append("Missing 'id' field")
    if not config.name:
        errors.append("Missing 'name' field")

    # Check bone hierarchy
    bone_ids = {b.id for b in config.bones}

    for bone in config.bones:
        if bone.parent and bone.parent not in bone_ids:
            errors.append(f"Bone '{bone.id}' has invalid parent '{bone.parent}'")

    # Check for cycles in bone hierarchy
    visited = set()
    for bone in config.bones:
        current = bone.id
        path = set()
        while current:
            if current in path:
                errors.append(f"Cycle detected in bone hierarchy: {bone.id}")
                break
            path.add(current)
            parent_bone = config.get_bone(current)
            current = parent_bone.parent if parent_bone else None

    # Check IK chains reference valid bones
    for ik in config.ik_chains:
        for bone_name in ik.chain:
            if bone_name not in bone_ids:
                errors.append(f"IK chain '{ik.name}' references unknown bone '{bone_name}'")

    return errors
